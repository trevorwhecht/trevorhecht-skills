---
name: trevskills-transcript-mining
description: Count process signals in headless scrum transcripts (turns, tokens and wall time per role, tool-call loops, repeated failing commands, re-reads, agents stuck before writing their .md, orchestrator retries), let Jev pick which outliers flailed, collect the user's scrum complaints from interactive chats, and write them all to transcript-signals.md for the scrum digest. Use for "transcript signals", "how did the scrum agents behave", or /trevskills-transcript-mining.
disable-model-invocation: true
allowed-tools: Bash(python3 *), Read, Edit
---

# Transcript signals

`transcript_signals.py` (next to this file) reads the Claude Code transcripts in
`~/.claude/projects` changed in the last 7 days. It computes every number in code, sends only the
outliers to Jev (`~/.claude/scripts/jev-rank.py`), and overwrites
`<trevskills-scrum repo>/scrum/digests/transcript-signals.md`. The scrum digest reads that file.

## Rule

This pass never writes scrum proposals, backlog items, or edits to agent files or SKILL.md files.
The digest reads transcript-signals.md and is the only thing that proposes scrum edits. Findings
go into the file's `## Notes` section and nowhere else.

## 1. Run

```bash
python3 ~/.claude/skills/trevskills-transcript-mining/transcript_signals.py
```

- Exit 2 (`no trevskills-scrum project registered`) → rerun with `--out <path>`, or report and stop.
- Other flags: `--days N`, `--top N` (default 5), `--no-jev`, `--projects-dir DIR`, `--jev PATH`.
- `Jev: unavailable` in the file → the top flails are in code order (most signals first). Carry on.

## 2. Read the top flails

Open the written file. For each of the first 3 lines under `## Top flails` (fewer if there are
fewer; `None` → skip to step 3):

1. Read that session's `.jsonl` path (the text after `—`). Look at the signals the line names:
   the repeated call, the failing command, the re-read file, or where the agent stopped.
2. Decide in one line what went wrong.

## 3. Write notes

Append a `## Notes` section at the end of the same file, with one line per session read:

```
## Notes
- <job id> · <role>: <what went wrong>
```

No sessions read → write `## Notes` with `None`. The script rewrites the whole file on its next
run, so notes never pile up.

## 4. Summary

Report the file path, the scrum and interactive session counts from its `Generated:` line, the
number of outliers, and the notes you wrote.
