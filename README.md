# lawdog

AI legal assistant plugin for Brazilian court workflows. Provides skills and tools for individuals navigating civil proceedings — evidence preparation, document handling, and procedural guidance.

## Install

### Claude Code (plugin)

```bash
claude --plugin-dir ./lawdog/plugin
```

Or install permanently via the plugin manager:

```bash
/plugin install https://github.com/mrbrandao/lawdog
```

Skills are namespaced as `/lawdog:<skill-name>`.

### Lola (AI Context Module)

```bash
lola mod add ./lawdog --module-content plugin
lola install lawdog
```

### OpenClaw

Skills are installed automatically by lola into `~/.openclaw/workspace/skills/`.

## Skills

### `video2forum`

Converts video evidence (.MOV, .MP4, .AVI, .MKV, etc.) to WebM — the format accepted by PROJUDI/TJPR for evidence uploads.

```
/lawdog:video2forum ~/docs/case/*.MOV
```

**Requirements:** `ffmpeg` in PATH, or set `FFMPEG=/path/to/ffmpeg`.

Download ffmpeg from one of these sources, extract, and export the variable:
- Official: https://www.ffmpeg.org/download.html
- Static Linux builds: https://johnvansickle.com/ffmpeg/

```bash
export FFMPEG=~/ffmpeg-7.0.2-amd64-static/ffmpeg
```

**Output format:** WebM (VP8 video 500 kbps + Vorbis audio quality 4).

## Plugin structure

```
lawdog/
├── plugin/
│   ├── .claude-plugin/
│   │   └── plugin.json             # Claude Code plugin manifest
│   ├── AGENTS.md                   # Module-level context (lola)
│   ├── skills/
│   │   └── video2forum/
│   │       ├── SKILL.md            # Skill definition (agentskills.io standard)
│   │       └── scripts/
│   │           └── video2forum.sh  # Conversion script
│   └── commands/                   # Slash commands (future)
└── README.md
```

## License

MIT
