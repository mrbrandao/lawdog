# Court Portals by State

Maps each state to its TJ, case tracking portal, and JEC access flow.
Read this file during case intake (Step 2b) to orient the user on their
specific court system.

## Paraná (PR)

**Tribunal de Justiça:** https://www.tjpr.jus.br/
**Acompanhamento de processos (PROJUDI):** https://projudi.tjpr.jus.br/projudi/
**Formulário JEC (distribuição):** https://www.tjpr.jus.br/formulario-virtual-juizados-especiais

### Como orientar o usuário (PR)

1. Acesse o formulário virtual do JEC no link acima
2. Selecione a **Comarca** (ex: Curitiba, Londrina, Maringá, Ponta Grossa)
3. Selecione a **Vara ou Juizado Especial** da comarca
4. Preencha e distribua a petição inicial pelo sistema online

Para acompanhar um processo já distribuído:
- Acesse o PROJUDI: https://projudi.tjpr.jus.br/projudi/
- Faça login com usuário e senha cadastrados, ou consulte por número do processo
  (consulta pública, sem login)

### Notas (PR)

- PROJUDI é o sistema eletrônico do TJPR — todos os atos processuais passam por ele
- Petições, anexos e intimações são enviados e recebidos pelo PROJUDI
- Vídeos de evidência devem estar em formato WebM — use `/lawdog:video2forum`
- Cada nova juntada gera um novo protocolo sequencial no PROJUDI

---

## Como adicionar outros estados

Para adicionar um estado, use o seguinte template:

```markdown
## [Estado por extenso] ([UF])

**Tribunal de Justiça:** [URL do TJ]
**Acompanhamento de processos:** [URL do portal]
**Formulário JEC:** [URL do formulário, se disponível online]

### Como orientar o usuário ([UF])

[passo a passo de distribuição e acompanhamento específico do estado]

### Notas ([UF])

[sistema usado, prazos específicos, observações relevantes]
```

Estados prioritários para implementação futura (por volume de causas JEC):
SP (e-SAJ/ESAJ), RJ (e-proc TJRJ), MG (SIMBA TJMG), RS (Themis/SAJ TJRS).
