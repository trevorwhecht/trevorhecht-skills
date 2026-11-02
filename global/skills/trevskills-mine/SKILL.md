---
name: trevskills-mine
description: Mine recent interactive Claude Code chats for unfinished work, facts the user taught that never reached an .md, and dropped findings. Jev ranks only the sessions new since the last run, one Opus reader reads the top ~20, and the results are queued as backlog items and knowledge saves. Use for "mine my transcripts", "what did we leave unfinished", or /trevskills-mine.
disable-model-invocation: true
allowed-tools: Bash(python3 *), Read, Grep, Glob, Agent
---

# Transcript mining

`mine.py` (next to this file) lists the interactive sessions that changed since the last run
(`~/.claude/transcript-mining/last-mined`, else the last 14 days), squeezes each to one line, and
asks Jev (`~/.claude/scripts/jev-rank.py`) three yes/no questions about it. Headless (`sdk-cli`)
scrum sessions and subagent transcripts are skipped. Act without asking for approval: backlog
items and knowledge-save jobs both pass scrum triage and review later.

Run the steps in order. Never skip to step 5 early.

## 1. Rank

```bash
python3 ~/.claude/skills/trevskills-mine/mine.py rank --exclude <current session id>
```

- Output `mine: no new sessions` → say "nothing new" and stop. Do not run `mark`.
- Exit 1 (`mine: jev-rank failed: ...`) → report the reason and stop. The marker stays put, so
  the next run covers these sessions again.
- Otherwise each line is `<score>\t<path>\t<date> | <cwd> | <session8> | ...`, best first, and the
  last line is `MARK <epoch>`. Keep the epoch for step 5. Zero ranked lines above `MARK` means
  nothing scored high enough: go straight to step 5.

## 2. One Opus reader

Spawn exactly one Agent with `model: "opus"`, passing it the ranked lines and this brief:

> For each session below, read it with `python3 ~/.claude/skills/trevskills-mine/mine.py text <path>`.
> Never open the raw .jsonl. Look for: work that was planned or started but not finished; a fact,
> rule or process the user taught that should live in a doc; a finding or problem that was noticed
> and then dropped. The repo for a session is its `cwd` with any `/.claude/worktrees/...` tail
> removed; confirm it from the chat. Return only lines of these two forms, nothing else:
>
> `BACKLOG | <repo path> | <one-line item> | <session8>`
> `SAVE | <fact> | <topic> | <session8>`
>
> Skip anything the chat itself finished, tracked or saved. Never propose edits to scrum agent
> files or SKILL.md files (the scrum digest owns process fixes; produce only BACKLOG and SAVE lines). No line → return nothing.

Ignore any reply line that matches neither form.

## 3. BACKLOG lines

For each `BACKLOG | <repo> | <item> | <session8>`:

1. `<repo>/scrum/backlog.md` missing → skip it and list it under **Reported** (repo has no scrum).
2. Read that backlog. An open (`- [ ]`) or done (`- [x]`) line that already covers the item →
   skip it as a duplicate.
3. Otherwise add it:
   ```bash
   python3 ~/.claude/skills/trevskills-scrum/board.py --dir <repo>/scrum backlog-add -- '<item> (chat <session8>)'
   ```
   Escape any `'` in the item as `'\''`.

## 4. SAVE lines

For each `SAVE | <fact> | <topic> | <session8>`, follow CLAUDE.md "Save what I teach" steps 1–4:

1. **Search first.** Find the most specific .md that already covers the topic: repo docs
   (`<repo>/docs/logic/*.md`), skill files, then `memory/`. Grep the headings.
2. **No repeats.** The file already says it → skip it as a duplicate.
3. **No contradictions.** It contradicts the file or the code → never write it. List it under
   **Reported** as `MD CONTRADICTION`, quoting both sides.
4. **Write or route.**
   - Target is a `memory/` note → write it directly, updating the existing note rather than
     starting a duplicate. A new topic gets a new note linked from MEMORY.md.
   - Target is inside a git repo (including skills symlinked into one) → never edit it here.
     Queue a knowledge-save job in that repo's backlog, the way CLAUDE.md does under cool down:
     ```bash
     python3 ~/.claude/skills/trevskills-scrum/board.py --dir <repo>/scrum backlog-add --top -- 'Lane: lilguy — knowledge save: <fact> → <file> "<section>" (chat <session8>)'
     ```
     Use `Lane: fast — knowledge save` instead when it adds more than ~30 lines or needs a new .md.
     The repo has no `scrum/backlog.md` → list it under **Reported**.

## 5. Mark

Only after every line from step 2 has been added, skipped or reported:

```bash
python3 ~/.claude/skills/trevskills-mine/mine.py mark <epoch from the MARK line>
```

## 6. Summary

End with three short lists: **Added** (backlog items and saves, each with its repo or file),
**Skipped** (duplicates, with the line that already covers each), and **Reported** (repos without
scrum, `MD CONTRADICTION`s). Then the number of sessions ranked and the new marker.

## 7. Archive

Dry run of the Drive archive (it changes nothing and never calls rclone):

```bash
python3 ~/.claude/skills/trevskills-mine/mine.py archive
```

It lists each interactive session (and the `subagents/` transcripts of sessions already archived) at or before the marker and older than 30 days as
`would archive <path> -> gdrive:claude-transcripts/<project>/<id>.jsonl.xz`. Report its final
`mine: ...` line as one more line after the summary.

`archive --apply` xz-compresses each listed session, uploads it with `rclone copyto`, and deletes the
local `.jsonl` only after the remote copy's size and md5 (`rclone lsjson --hash`) match. It needs
rclone with a `gdrive:` remote. It is not part of the weekly run yet: never pass `--apply` here.

## Weekly run

Runs once a week unattended as `claude -p "/trevskills-mine"` (a LaunchAgent the user sets up). The
`last-mined` marker keeps each run to sessions newer than the previous one. An unattended run uses
no `--exclude`. The pass never proposes scrum agent or SKILL.md edits; it only produces backlog
items and knowledge-save jobs. Sessions started with `/trevskills-scrum` are skipped.
Step 7 runs the archive as a dry run only.
