---
name: trevskills-owa-usage
description: Use when the user asks for "OWA usage", "usage per Mac", how the OWA Claude account's weekly limit or $200 plan splits between the two Macs, or runs /trevskills-owa-usage.
---

# OWA usage per Mac

The OWA Claude account (config dir `~/.claude-owa`) is shared by this Mac and one other Mac. This skill shows how much of the current OWA week each Mac used.

## Run

```bash
python3 ~/.claude/skills/trevskills-owa-usage/owa_usage.py week
```

Print its output as-is, with no rewording. It shows, per Mac, the weighted tokens, share, points of the account 7d % and $ (plan $200 × share), then `7d: <pct>% (as of <time>)` from `~/.claude-owa/usage.json`. If the other Mac is asleep it prints `other Mac unreachable` and this Mac at 100%.

## How it counts

- OWA week: Wednesday 11:00 local to the next Wednesday 11:00.
- Assistant records in `~/.claude/projects/**/*.jsonl` inside the window, deduped by `(message.id, requestId)`.
- Weighted = input × 1 + output × 5 + cache write × 1.25 + cache read × 0.1.
- This Mac counts only sessions listed in `~/.claude-owa/session-env` (`--owa-only`). The other Mac (`user@users-MacBook-Air.local`; override with `OWA_USAGE_OTHER`, empty = no other Mac) is reached over `ssh` and counts all its sessions.

## Other commands

- `owa_usage.py report`: upserts this week's row in `~/Library/Mobile Documents/com~apple~CloudDocs/Claude Usage/YYYY-MM.md` (the month of the week's end date). The top line splits the month's $200 by Mac; each row holds tokens, shares, the account 7d %, each Mac's $ (200 × week weighted / month weighted, split by share) and a status: `in progress`, `other Mac pending` or `final`. Every non-`final` row is recounted on each run.
- `owa_usage.py install`: writes `~/Library/LaunchAgents/com.trevskills.owa-usage.plist` and loads it. It runs `report` hourly and on Wednesday at 10:55. Logs go to `~/Library/Logs/owa-usage.log`.
- `owa_usage.py count --since ISO --until ISO [--owa-only]`: raw JSON totals (what `ssh` runs on the other Mac).
