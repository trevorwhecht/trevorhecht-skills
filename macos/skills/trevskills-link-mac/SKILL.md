---
name: trevskills-link-mac
description: Use when the user asks to "link a new Mac", "add a worker computer", "set up the new Mac for scrum", or wants another Mac to run scrum jobs for this one.
---

# Link another Mac as a scrum worker

Brings a new Mac online as a scrum worker with one human visit to it. The automated part lives in the trevskills-scrum repo: `skills/trevskills-scrum/shop.py` and `skills/trevskills-scrum/lanes/shop.md` (`shop.py setup`). Read those; do not restate them here. Below are the steps before and around it. `<alias>` = the ssh alias, `<name>` = the Mac's hostname.

## Steps

1. **Specs, once.** One iMessage handoff to the Mac's Apple ID asking for model, macOS, RAM, user name, IP. Trevor pastes it into that Mac's Claude. Never more than one trip to the machine.
2. **The one visit, on that Mac:** turn on Remote Login; append this Mac's `~/.ssh/id_rsa.pub` to its `~/.ssh/authorized_keys`; install Claude Code and sign in both accounts (main, and OWA with `CLAUDE_CONFIG_DIR=~/.claude-owa`); install Google Chrome (Playwright refuses its own Chromium on older macOS but works with `channel: "chrome"`).
3. **Here:** add to `~/.ssh/config`: `Host <alias>`, `HostName <name>.local`, `BatchMode yes`. Ask Trevor, then add the allow rule `Bash(ssh <alias>:*)` to `~/.claude/settings.local.json` (auto mode blocks any other remote exec). Optional Tailscale: join as `tag:shop` with no outgoing grants so the worker cannot see this Mac's dashboard.
4. **Headless login.** SSH cannot read the remote login Keychain (`security` rc 36), so `claude -p` over SSH says "Not logged in" even when the GUI is signed in. Never conclude "not logged in" from SSH alone. Fix: a long-lived `claude setup-token` per account, saved mode 600 as `~/.claude-owa/oauth-token` and `~/.claude/oauth-token` on that Mac. No visit needed:
   - Run `python3 ~/.claude/skills/trevskills-link-mac/setup_token.py <alias> owa` (then `main`) in the background. It runs `setup-token` over `ssh -tt` in a pty and writes the sign-in URL to `/tmp/link-mac-<alias>-<account>/url.txt` (it prints `URL ready`).
   - Open that URL in this Mac's signed-in Chrome (the profile for that account, see `reference_chrome_profiles.md`), click Authorize, read the code from the platform.claude.com callback page, write it to `code.txt` in the same folder.
   - The script types the code (Enter as a separate write: Ink reads one chunk ending in `\r` as a paste) and pipes the token straight into the remote file. It never prints the token; never read it out.
   - Verify: `ssh <alias> 'CLAUDE_CODE_OAUTH_TOKEN="$(cat ~/.claude-owa/oauth-token)" CLAUDE_CONFIG_DIR=~/.claude-owa claude -p "reply with the word ok" --model haiku --max-turns 1'` answers ok (main: `~/.claude/oauth-token`, no config dir). Use the full path to `claude` if it is not on the non-interactive PATH.
5. **Then** `python3 ~/.claude/skills/trevskills-scrum/shop.py setup`, repeated until every step is ok.
6. **One worker only.** `shop.py` supports a single alias (`ALIAS = "shopmac"`). A second worker Mac needs the trevskills-scrum backlog item "support more than one worker Mac" first; say so to Trevor instead of linking it.

## Gotchas

- The token must be matched before newlines are stripped from the pty output, or the next line ("Store this token securely") glues onto it. The script does this.
- The shop-style Mac's non-interactive SSH shell has no node, gh or claude on PATH.
