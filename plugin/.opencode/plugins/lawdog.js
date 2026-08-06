/**
 * Lawdog plugin for OpenCode.ai
 *
 * - config hook: registers plugin/skills/ so OpenCode discovers all lawdog skills
 *   without symlinks or manual opencode.json edits
 * - transform hook: injects Dr. LawDog session context + active case detection
 *   into the first user message of each new conversation
 * - sets process.env.LAWDOG_PLUGIN_DIR so SKILL.md bash scripts find their
 *   scripts directory when CLAUDE_SKILL_DIR is not set (Claude Code sets it;
 *   OpenCode does not)
 *
 * Pattern mirrors superpowers/.opencode/plugins/superpowers.js
 */

import path from 'path';
import fs from 'fs';
import os from 'os';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// .opencode/plugins/lawdog.js — two levels up → plugin/ root
const PLUGIN_DIR = path.resolve(__dirname, '../..');
const SKILLS_DIR = path.join(PLUGIN_DIR, 'skills');

// Expose to bash scripts as fallback when CLAUDE_SKILL_DIR is not set.
// Claude Code sets CLAUDE_SKILL_DIR per skill; OpenCode does not.
// SKILL.md files use: ${CLAUDE_SKILL_DIR:-${LAWDOG_PLUGIN_DIR}/skills/<name>}
process.env.LAWDOG_PLUGIN_DIR = PLUGIN_DIR;

// Cache AGENTS.md content across the plugin lifetime (file doesn't change
// while OpenCode is running). Active case detection is always fresh (called
// once per conversation, not once per agent step, because of the transform guard).
let _agentsContent = undefined;

/**
 * Read plugin/AGENTS.md once and cache the result.
 */
const readAgents = () => {
  if (_agentsContent !== undefined) return _agentsContent;
  const agentsPath = path.join(PLUGIN_DIR, 'AGENTS.md');
  _agentsContent = fs.existsSync(agentsPath)
    ? fs.readFileSync(agentsPath, 'utf8').trim()
    : '';
  return _agentsContent;
};

/**
 * Scan LAWDOG_CASES_DIR for cases with a pending action in caso.md.
 * Returns a formatted markdown string for inclusion in session context.
 *
 * Called once per new conversation (the transform guard prevents re-injection
 * on subsequent agent steps within the same conversation).
 */
const detectActiveCases = () => {
  const casesDir = process.env.LAWDOG_CASES_DIR
    ? process.env.LAWDOG_CASES_DIR
    : path.join(os.homedir(), 'lawdog-cases');

  if (!fs.existsSync(casesDir)) {
    return `Nenhum caso ativo encontrado em \`${casesDir}\`.`;
  }

  const activeCases = [];
  try {
    const entries = fs.readdirSync(casesDir, { withFileTypes: true });
    for (const entry of entries) {
      if (!entry.isDirectory()) continue;
      const casoPath = path.join(casesDir, entry.name, 'caso.md');
      if (!fs.existsSync(casoPath)) continue;
      const content = fs.readFileSync(casoPath, 'utf8');
      // Extract the line after "Ação pendente:"
      const match = content.match(/Ação pendente:[^\n]*\n([^\n]+)/);
      if (match) {
        const pending = match[1].trim();
        if (pending && pending !== '—') {
          activeCases.push(`- **${entry.name}**: ${pending}`);
        }
      }
    }
  } catch (_) {
    // Non-fatal: permission errors or malformed files
  }

  if (activeCases.length === 0) {
    return `Nenhum caso ativo encontrado em \`${casesDir}\`.`;
  }
  return (
    `## Casos em andamento\n${activeCases.join('\n')}\n\n` +
    `Retome com a skill \`caso\` ou registre nova movimentação com a skill \`movimentacao\`.`
  );
};

/**
 * Build the full session context string injected into each conversation.
 * Static persona is cached; active cases are detected fresh per conversation.
 */
const buildContext = () => {
  const persona = readAgents();
  const caseSection = detectActiveCases();

  return `<lawdog-session-context>
<MANDATORY_RULE>
Você é o Dr. Andre LawDog. ANTES de gerar qualquer resposta, verifique se uma skill lawdog se aplica à mensagem do usuário. Se aplicável, invoque a skill via Skill tool PRIMEIRO — não gere resposta antes disso. Isso não é opcional.

Triggers obrigatórios:
- Usuário descreve problema jurídico, quer processar alguém, ou menciona JEC → skill: caso
- Usuário menciona nova decisão do juiz, intimação, ou documento do PROJUDI → skill: movimentacao
- Usuário quer organizar evidências, fotos, PDFs, vídeos para o processo → skill: juntada
- Usuário tem caso já em andamento sem organização lawdog → skill: importar-caso
- Usuário quer redigir/escrever/gerar a petição do caso → skill: peticao
- Usuário quer converter imagem para PDF → skill: img2pdf
- Usuário quer converter documento para PDF → skill: doc2pdf
- Usuário quer converter vídeo para formato do PROJUDI → skill: video2forum
- Usuário pede texto atualizado de artigo jurídico → skill: fetch-law

Quando não há skill aplicável (conversa casual, dúvida geral sem ação específica): responda diretamente como Dr. LawDog.
</MANDATORY_RULE>

${persona}

## Contexto de instalação (OpenCode)

LAWDOG_PLUGIN_DIR: ${PLUGIN_DIR}
Protocolos: ${PLUGIN_DIR}/protocols/
Conhecimento jurídico: ${PLUGIN_DIR}/knowledge/
Templates: ${PLUGIN_DIR}/templates/

Ao referenciar um arquivo de protocolo ou conhecimento durante um skill, use os caminhos absolutos acima.

## Skills disponíveis

| Skill | Quando invocar |
|---|---|
| \`caso\` | Abrir caso novo OU retomar caso existente |
| \`movimentacao\` | Nova decisão/doc do PROJUDI chegou |
| \`juntada\` | Organizar evidências em \`anexos/\` → \`juntada/\` |
| \`importar-caso\` | Caso já existente sem organização lawdog |
| \`peticao\` | Redigir a petição inicial ou subsequente |
| \`img2pdf\` | Converter imagem → PDF |
| \`doc2pdf\` | Converter documento → PDF |
| \`pdf-split\` | PDF > 4MB → partes |
| \`doc2docx\` | Markdown → DOCX editável |
| \`video2forum\` | Vídeo → MP4/WebM (PROJUDI) |
| \`fetch-law\` | Buscar artigo jurídico atualizado |

## Seleção de modelo por tarefa

**Haiku** — conversão de arquivos (img2pdf, doc2pdf, video2forum), operações de arquivo, pdf-split.
**Sonnet** — triagem jurídica, leitura de decisões, análise de evidências, orientação de próximos passos.
**Opus** — redação de petições, casos complexos, simulação adversarial profunda.

## Fluxo de trabalho

Novo caso: **caso** → **juntada** → **doc2pdf** → upload PROJUDI
Caso existente: **movimentacao** → **juntada** → **doc2pdf** → upload PROJUDI
Caso desorganizado: **importar-caso** → **juntada** → continua normal

${caseSection}
</lawdog-session-context>`;
};

export const LawdogPlugin = async ({ client, directory }) => {
  return {
    /**
     * Register the skills directory so OpenCode discovers all lawdog skills
     * without requiring symlinks or manual config.skills.paths edits.
     */
    config: async (config) => {
      config.skills = config.skills || {};
      config.skills.paths = config.skills.paths || [];
      if (!config.skills.paths.includes(SKILLS_DIR)) {
        config.skills.paths.push(SKILLS_DIR);
      }
    },

    /**
     * Inject Dr. LawDog context into the first user message of each conversation.
     *
     * The hook fires on every agent step. The guard `lawdog-session-context`
     * prevents re-injection on subsequent steps within the same conversation
     * (same pattern as superpowers using-superpowers guard).
     */
    'experimental.chat.messages.transform': async (_input, output) => {
      if (!output.messages.length) return;
      const firstUser = output.messages.find((m) => m.info.role === 'user');
      if (!firstUser || !firstUser.parts.length) return;

      // Guard: skip if already injected in this conversation
      if (
        firstUser.parts.some(
          (p) => p.type === 'text' && p.text.includes('lawdog-session-context')
        )
      )
        return;

      const context = buildContext();
      const ref = firstUser.parts[0];
      firstUser.parts.unshift({ ...ref, type: 'text', text: context });
    },
  };
};
