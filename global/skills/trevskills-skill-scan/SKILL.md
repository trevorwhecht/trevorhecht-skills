---
name: trevskills-skill-scan
description: Security scan of Claude Code skills, agents and plugins with NVIDIA SkillSpector (static checks only, no API key) for prompt injection, hidden instructions, data and key exfiltration and other malicious patterns. Use when the user says "scan my skills", asks "is this skill safe", and before installing any skill, plugin or agent (scan its path or git URL first).
allowed-tools: Bash(bash *), Read
---

# Skill scan

A skill runs with the agent's full trust, so one hidden instruction (an HTML comment telling the agent to send an
API key to a URL) is enough to leak secrets. In NVIDIA's study of 31,132 public skills, about 1 in 4 had a
vulnerability and about 1 in 20 looked malicious. SkillSpector (https://github.com/NVIDIA/skillspector, Apache 2.0)
reads a skill without running it and scores it 0 to 100: 0-20 SAFE, 21-50 CAUTION, 51+ DO_NOT_INSTALL.

## Run

```bash
bash ~/.claude/skills/trevskills-skill-scan/scan.sh                 # everything installed
bash ~/.claude/skills/trevskills-skill-scan/scan.sh <path | git URL> # one, before it is installed
```

- **No argument:** every skill in `~/.claude/skills` (symlinks followed, nested synced skills included), every
  agent in `~/.claude/agents` and every plugin listed in `~/.claude/plugins/installed_plugins.json`, and the same
  under `~/.claude-owa`. Each real folder or file is scanned once, four at a time. About 100 targets take several
  minutes: run it in the background and read the tail.
- **Path or git URL:** scans only that skill, plugin or agent. For a marketplace plugin, scan its source folder under
  `~/.claude/plugins/marketplaces/<marketplace>/` or its repo URL before `/plugin install`.
- The first run installs SkillSpector with `uv tool`, pinned to the exact release in `SS_VERSION` / `SS_COMMIT`.
- Output: `~/Developer/claude/skill-scans/<date>.md` (a one-target scan writes `<date>-<name>.md`, so it never
  replaces the day's full scan), worst first: name, kind, path, score, verdict, top findings. `(partial)` after a
  verdict means part of it could not be fully parsed. The script prints the report path and every do-not-install
  name with its path. Exit 0 nothing flagged, 1 something is DO_NOT_INSTALL, 2 a scan failed.

## Before installing a skill, plugin or agent

1. Run `scan.sh <path or URL>` first. Never install before the scan finishes.
2. **DO_NOT_INSTALL:** do not install. Show the user the top findings and let them decide.
3. **CAUTION:** show the findings and install only if the user says yes.
4. **SAFE:** go ahead.

## Reading a hit

Static checks match patterns, not intent: a skill that documents `rm -rf`, reads `.env` on purpose or calls `curl`
scores high too. For each DO_NOT_INSTALL row, open the file:line in the finding and look for the real red flags:
instructions inside HTML comments or other hidden text, text telling the agent to send keys, env vars or files to a
URL, base64 or other encoded blobs, `curl | sh` installers, and hooks that make network calls. Full detail for one
target: `skillspector scan --no-llm <path>`.

## Rules

- Read-only. Never uninstall, move or edit a scanned skill, agent or plugin, even a DO_NOT_INSTALL one: list the
  hits and let the user decide.
- Static only. scan.sh always passes `--no-llm`; never set `SKILLSPECTOR_PROVIDER` or an API key for it (the LLM
  pass sends file contents to a paid API). The supply-chain check still asks OSV.dev, which is free and keyless,
  about declared package names.
- Bump the pin on purpose: set `SS_VERSION` and `SS_COMMIT` from a SkillSpector release tag, never to `main`.
