---
name: trevskills-mac-cleanup
description: Use when a Mac is low on disk space, "System Data" is huge, running slow / sluggish, high CPU or memory use, or the user wants to reclaim space or clean up processes — clearing caches, Adobe/Photoshop/Illustrator junk, stray "Asset" export files, offloading large files to iCloud, auditing questionable system data, reviewing/quitting running processes, or checking for malware/adware persistence. Also covers fixing iCloud Contacts not syncing to the Mac.
---

# Mac Cleanup

## Overview

Reclaims disk space and audits a Mac safely. **Dry-run first, always.** Regenerable caches are deleted; user files (the "Asset" sweep) are moved to Trash, never `rm`'d; the audit is fully read-only; iCloud offload keeps files in the cloud. Message CONTENT and credentials are never touched.

Two engines in this folder:
- `trevskills-mac-cleanup.sh` — cache cleanup, Asset sweep, iCloud offload. Dry-run by default.
- `deep-audit.sh` — read-only audit: malware/persistence, questionable system data, large files.

## ALWAYS end every session with the report (required)

Trevor wants a **full report every single time this skill is used**. Workflow:

1. **Before** applying any cleanup, capture the baseline free space:
   `df -k /System/Volumes/Data | tail -1 | awk '{print $4}'`  → remember this number (KB).
2. Do the work (clean / assets / offload / snapshots / audit, etc.).
2b. **Always include the process reset** — Trevor wants RAM/CPU hogs reset on every cleanup, not just disk reclaimed:
   `./trevskills-mac-cleanup.sh processes reset` (dry-run, show him the list) → `--apply`.
   This is the cheap alternative to a reboot: it clears a spinning helper without closing his work. Note it in the report.
2c. **Always run the asset sweep, and apply it** (decided 2026-08-24 — he wants this automatic, no approval step).
   **Why it's safe to automate:** `Asset N` files are throwaway exports Trevor generates from his `.ai` masters purely for quick sharing — the `.ai` file is the source of truth and always survives. They are temp files by definition, so there is nothing to preserve and no reason to ask. Regenerating one is a re-export, not a recovery.
   `./trevskills-mac-cleanup.sh assets scan` → then `./trevskills-mac-cleanup.sh assets trash --apply`.
   Run the `scan` first anyway and **print the file list in the report** — not as a gate, but so there's a record of what was removed.
   This applies **in shared iCloud folders too** — he was shown that removals there propagate to collaborators and chose it deliberately. Do not re-litigate it each run.
   Files always go to `~/.Trash` (recoverable ~30 days), never `rm` — that safety property is what makes the automatic sweep acceptable, so never "optimize" it into a delete.
3. **End with:** `./trevskills-mac-cleanup.sh report <baseline_kb>` — pass the baseline so it shows "Freed THIS session". If the session did no cleanup (just a checkup), run `report` with no argument.
4. **Present the whole report to Trevor**, including: GB freed, memory/uptime summary, and the maintenance plan (restart cadence + how often to run this skill).

The report persists free-space + timestamp to `~/.mac-cleanup/last-run`, so each run also shows change-since-last-run and derives the recommended cleanup frequency from the actual fill rate. Never skip the report — it is the point of running the skill for Trevor.

## Safety model

- **Cache purge** never touches `~/Documents`, `~/Desktop`, `~/Downloads`, `~/Developer`, `~/Pictures`, `~/Movies`, `.ssh`, `.gnupg`, Keychains, `~/Library/Messages` content, or any `*.photoslibrary`.
- **Asset sweep** moves to `~/.Trash` (recoverable ~30 days). Matches ONLY Illustrator default-export names (`Asset`, `Asset 3`, `Asset 15@300x`); excludes `*.photoslibrary`, `~/Library`, keys, `node_modules`, `.git`, `*FINAL*`.
- **Audit changes nothing.** It reports and raises questions; the user decides.
- **Offload** keeps the file in iCloud and only evicts the local copy (re-downloads on demand).

## Quick reference

| Command | What it does |
|---|---|
| `./trevskills-mac-cleanup.sh scan` | Report reclaimable cache space per category. No changes. |
| `./trevskills-mac-cleanup.sh clean [--apply]` | Dry-run (or apply) the safe cache set. |
| `./trevskills-mac-cleanup.sh clean system-caches --apply` | Aggressive: sweep remaining `~/Library/Caches`. |
| `./trevskills-mac-cleanup.sh assets scan` | List scoped `Asset` export files + size. |
| `./trevskills-mac-cleanup.sh assets trash --apply` | Move those to Trash. |
| `./trevskills-mac-cleanup.sh clean build-caches --apply` | Delete Next.js/Turbo `.next`/`.turbo` build caches under `~/Developer` (auto-rebuild). |
| `./trevskills-mac-cleanup.sh snapshots` | Thin Time Machine local snapshots (prompts for admin password — never stored). |
| `./trevskills-mac-cleanup.sh audit [security\|malware\|extensions\|systemdata\|largefiles\|all]` | Read-only deep audit. |
| `./trevskills-mac-cleanup.sh audit extensions` | Every Chrome extension per profile, with flags: free VPN/proxy, coupon/cashback, crypto wallet, AI/SEO page reader, access to every site. |
| Connected accounts (OAuth) audit | Chrome-driven walk of Spotify, Google, Facebook, Instagram and GitHub app grants. Run it with any security/malware check; see the section below. |
| `./trevskills-mac-cleanup.sh audit malware` | Deep sweep: crypto-verify persistence, hosts/cron/login-items/DYLD, network listeners, recent drops. |
| `./trevskills-mac-cleanup.sh report [baseline_kb]` | Full run report: GB freed, memory/uptime, and a personalized maintenance + restart + frequency plan. |
| `./trevskills-mac-cleanup.sh processes` | Read-only: uptime/swap, top CPU + memory, per-app aggregates, and a signature-based malware flag. |
| `./trevskills-mac-cleanup.sh processes quit [--apply]` | Quit ONLY safe background helpers (Adobe CC services); suggests user apps to close manually. |
| `./trevskills-mac-cleanup.sh processes reset [--apply]` | Reset stuck **Apple** helpers over threshold (BlastDoor, transcoder, media analysis…). They auto-relaunch. |
| `./trevskills-mac-cleanup.sh processes reset --self-check` | Verify the never-kill denylist still fires. Run after ANY edit to that list. |
| `./trevskills-mac-cleanup.sh offload evict "<path>"` | Free local copy of an iCloud-Drive file (stays in cloud). |
| `./trevskills-mac-cleanup.sh offload move "<path>" [--apply]` | Move a local file into iCloud Drive, then evict. |
| `./trevskills-mac-cleanup.sh archive "<src>" "<archive>" [months] [--apply]` | Move files in `<src>` not modified in `<months>` (default 6) into `<archive>` (a sibling folder), for offloading. |

Cache categories: `app-caches` `dev-caches` `adobe-caches` `messages-cache` `logs` `system-caches` `build-caches`. Default `clean` = the safe set (not `system-caches`/`build-caches`).

**NEVER store passwords.** The `snapshots` step uses `sudo` and must let macOS prompt for the password interactively every run. Do not hardcode a password anywhere in this skill — a plaintext admin password in a file is a full-system credential leak.

**Always** dry-run and show the list before any `--apply` — with one deliberate exception: **`assets` no longer needs approval** (Trevor's call, 2026-08-24). Still print the scanned list in the report so there's a record, but apply without waiting. Everything else (cache purge, offload, archive, snapshots) keeps the dry-run-then-approve gate.

Note Desktop/Documents are usually iCloud-synced, and some folders (e.g. `~/Desktop/Mockups`) are **shared with clients** — trashing there propagates to collaborators as well as his other devices. He was shown this and opted in anyway; files land in `~/.Trash` and are recoverable ~30 days. Say what was removed in the report; don't stop to ask.

## Deep audit (read-only)

`./trevskills-mac-cleanup.sh audit all` surfaces three things; act on nothing without the user:

1. **Security / malware** — SIP, Gatekeeper, XProtect version; LaunchAgents/Daemons (flags non-standard vendors); config profiles; third-party kernel/system extensions; known adware paths; browser extensions. `audit malware` goes deeper: it **cryptographically verifies** (`codesign --verify --strict`) every persistence binary — catching tampered/orphaned/missing targets a presence check misses — plus `/etc/hosts`, cron, login items, DYLD injection, non-loopback network listeners, and recently-dropped executables. **Known-benign noise to NOT alarm the user about:** Homebrew binaries and open-source DBs (Firebird, Postgres) are legitimately unsigned; Adobe bundles fail `--strict` on symlinks; Karabiner trips on xattr detritus; a plist pointing to a *missing* binary is almost always an uninstalled app's leftover, not malware. It's still a *persistence + integrity* review, not a threat-DB scan — for definitive certainty point the user to Objective-See KnockKnock or Malwarebytes.
2. **Questionable system data** — iOS backups, Xcode DerivedData/DeviceSupport/Archives, simulators, Docker, Containers/Group Containers, Time Machine local snapshots (`sudo tmutil thinlocalsnapshots / 999999999999 4`), leftover installers. Sizes only; user chooses.
3. **Large files > 500 MB** (`LARGE_MB=1000 ... audit largefiles` to raise the bar) — real local files (already-evicted iCloud files are skipped), flagged as offload candidates.

Note: `com.apple.MobileSMS` container + `~/Library/Messages` are Messages storage — they shrink via the Messages app's own "Keep Messages" setting, not this tool.

## Connected accounts (OAuth) audit

The Mac scans can't see this. Apps a user once signed into with Spotify, Google or Facebook keep their permissions on the provider's servers until removed, and they can act without anything running on the Mac. Example: a follow-to-download music tool keeps "manage who you follow" forever, so podcasts or artists show up followed without the user doing it. Whenever the user reports an account acting on its own, or asks for a security/malware check, run `audit extensions` and walk this list with the claude-in-chrome tools:

1. **Spotify** `https://www.spotify.com/account/apps/`: remove follow-gate, promo and contest tools, and anything the user doesn't recognise. Then offer **Sign out everywhere** (account overview).
2. **Google** `https://myaccount.google.com/connections?authuser=N` for every signed-in account (N = 0, 1, 2 …). Filter by **Access to**: apps with data access (Gmail, Drive, Calendar) matter. "Sign in with Google" only is low risk. Remove via the app → **Delete all** → **Confirm**.
3. **Facebook** `https://www.facebook.com/settings/?tab=applications`: only **Active** entries can still act; Expired ones can't. Remove → confirm in the dialog. Clicking the dialog's Remove by element ref can fail silently: click by coordinates from a screenshot, then reload and check the app is gone.
4. **Instagram** `https://www.instagram.com/accounts/manage_access/`.
5. **GitHub** `https://github.com/settings/applications` (Authorized OAuth Apps and GitHub Apps).
6. **Meta Accounts Center** → Password and security → **Where you're logged in**: look for locations or devices the user doesn't know, and for logins Meta flags as unrecognised.

Rules: list what you find first, then remove only what the user approves. Never sign in or enter a password; if a page wants one, hand it to the user. Extension removal stays manual, because automation can't open `chrome://extensions`: give the user the extension and profile names from `audit extensions`.

## Processes & slowness (running slow, high CPU/memory)

`./trevskills-mac-cleanup.sh processes` is read-only — it reports uptime, swap used, compressed RAM, top CPU + memory processes, per-app aggregate memory (Adobe/Chrome/etc.), and flags any running binary that lacks a valid Apple/Developer-ID signature (the malware check).

**Diagnose the cause before quitting anything — quitting apps is usually NOT the real fix:**
- **Uptime + swap is the #1 lever.** Many days of uptime with GBs of swap used and a full memory compressor means RAM has been churning to disk for weeks. **A restart clears all swap and the compressor instantly** — a far bigger win than quitting any single app. The report prints a RESTART RECOMMENDED banner when uptime ≥ 7 days or swap ≥ 2 GB.
- **Dual heavy apps.** Illustrator + Photoshop open at once (plus Adobe's login-launched background services) is a legitimate multi-GB load. That's expected, not a leak.

**Resetting stuck Apple helpers (`processes reset`) — run this every cleanup:**

Different from `quit`. These are launchd/XPC services that **relaunch themselves within seconds**, so killing one is a *reset*, not a quit — no user data, nothing stays dead. They're the usual cause of "one process pegged at 100% CPU for hours": they retry a bad input (a huge attachment, an undecodable message, a stuck photo analysis) forever, and the retry loop survives everything except a fresh process. A reboot fixes it — but so does this, without closing your work.

Covered: `MessagesBlastDoorService`, `IMTranscoderAgent`, `identityservicesd`, `mediaanalysisd`, `photoanalysisd`, `cloudd`, `contactsd`, `suggestd`, `spotlightknowledged`.

Only processes **over threshold** are reset (default CPU ≥ 20% or RSS ≥ 500 MB; override with `RESET_CPU_PCT=` / `RESET_RSS_MB=`). Healthy idle daemons are left alone — killing those just churns and re-warms caches for nothing.

> **⚠️ The never-kill denylist is the critical part of this feature.** `WindowServer` normally sits at 20–35% CPU (window compositing, external displays) and **will** trip any CPU threshold. Killing it force-logs the user out and loses every unsaved document. `launchd` panics the kernel; `loginwindow`/`securityd`/`opendirectoryd` end the session. The denylist is tested **before** the threshold check, never after. After editing `NEVER_RESET_RE` or `RESET_PROCS`, run `processes reset --self-check` — if it fails, do NOT run `--apply`.

**Quitting — safe by default:**
- `processes quit` (dry-run) → `--apply` quits ONLY background helpers that hold no user data (Creative Cloud UI/CCX/CCLibrary/Adobe Desktop Service) and relaunch automatically. Frees a few hundred MB.
- It **never** auto-quits Illustrator, Photoshop, editors, terminals, or browsers — unsaved work / open tabs. Those are printed as manual `osascript ... to quit` suggestions the user runs if they choose.
- **Malware flag:** on this machine everything is validly signed (Adobe, Google, Spotify, Epson, Karabiner, DisplayLink, ProtonVPN, Figma, and AccuRIP Emerald / `com.bluironictechnologies.RipEngine` — the screen-print film RIP). Any `>>> UNSIGNED/UNKNOWN` line is a real "investigate this" signal; for a true scan, point to Objective-See KnockKnock or Malwarebytes.
- Implementation note: the signature check captures `codesign` output to a variable and matches with `case` — piping into `grep -q` races under `set -o pipefail` (grep's early exit SIGPIPEs codesign → false "unsigned" flags).

## iCloud offload (free local space, keep the file)

- File already in Desktop/Documents/iCloud Drive → `offload evict "<path>"` tries to release the local copy; iCloud keeps it.
- Local file elsewhere → `offload move "<path>"` (dry-run) → `--apply` moves it into `iCloud Drive/Offloaded/`.
- Stale-folder archiving → `archive "<src>" "<archive>" 6 --apply` moves files not touched in 6 months into a sibling archive folder.

**CRITICAL LIMITATION — offload is a two-step, Finder-finished operation on modern macOS:**
Files with a "Keep Downloaded" pin carry the protected xattr `com.apple.fileprovider.pinned#PX`. Under the FileProvider system (Sonoma+), that pin can ONLY be cleared in Finder — `brctl evict` is a legacy no-op, `fileproviderctl` has no evict verb, and `xattr -d` can't remove a `#PX` attribute. So the CLI reliably **moves** files but cannot **offload** pinned ones. After `archive --apply` (or `offload`), tell the user to finish in Finder:

> **Right-click the archive/target folder → "Remove Download."**

That clears the pin, offloads everything in one shot, frees the local space, and keeps the files in iCloud (they re-download on open). Verify with `stat -f%b <file>` → `0` blocks means offloaded. Note: a pin is folder-recursive, so an archive folder must be a SIBLING of the pinned source, never a child.

## Messages (not automated — pointer only)

Trimming old messages is done by the user in **Messages → Settings → General → Keep Messages** (30 Days / 1 Year / Forever). With Messages-in-iCloud ON, that deletion syncs to all devices. This tool deliberately does **not** touch Messages content — only the regenerable `messages-cache` category clears the local cache.

## Contacts: new iPhone contacts not showing on the Mac (hard-won lessons)

**Root cause is usually disk pressure.** When the startup disk fills up, CloudKit (which syncs Contacts + Messages) wedges — and it STAYS wedged after you free space. Symptom: new contacts exist on iCloud.com/iPhone but never reach the Mac, and Messages shows raw numbers instead of names for those people (Messages reads the Mac's local Contacts — if the contact isn't there, no name).

**Diagnose before touching anything:**
1. Search the Mac's contact DB for the number:
   `sqlite3 -readonly ~/Library/Application\ Support/AddressBook/Sources/*/AddressBook-v22.abcddb "SELECT ZFULLNUMBER FROM ZABCDPHONENUMBER WHERE REPLACE(REPLACE(REPLACE(REPLACE(ZFULLNUMBER,' ',''),'(',''),')',''),'-','') LIKE '%<digits>%';"`
2. Check **iCloud.com/contacts** for the same person. If it's there but not on the Mac → Mac sync is wedged.

**Escalation ladder — try cheap fixes, STOP before the expensive ones:**
1. Toggle Contacts OFF (Keep on My Mac) → wait 15s → ON, in System Settings → iCloud → See All.
2. Daemon kick: `killall contactsd cloudd` (restarts sync — safe).

**⚠️ DO NOT casually escalate past here.** Both of the following BURNED the user for ~1 hour and did NOT fix a genuinely-wedged sync:
- **Removing `~/Library/Application Support/AddressBook`** to "force re-download" — the re-download STALLS partway (e.g. 203 of 1800) when CloudKit is wedged, leaving contacts missing. If you ever do this, **back up first** (`cp -R` the dir) and **export a vCard** (below).
- **Full iCloud sign-out/in** — also stalls partway AND, if Desktop & Documents Folders sync is on, **empties the local Desktop** (files stay safe in iCloud; a new empty Desktop is created — reassure, don't panic; sign back in to restore). Not worth it.

**When the sync stalls partway even after the above, it's a server-side CloudKit fault — only Apple can fix it.** Tell the user to call Apple Support: *"iCloud Contacts sync stalls at a partial download on my Mac, persists after sign-out/in; please reset my CloudKit Contacts zone."* Meanwhile, the reliable per-contact workaround is **AirDrop the contact card from phone → Mac** (bypasses sync entirely).

**Always make a safety copy before any destructive contacts step** — export all contacts to a portable vCard from the backup DB (names + phones + emails), so nothing is ever truly lost.

## Common mistakes

- `--apply` without showing the dry-run first. Don't.
- Blanket `*asset*` matching — catches Photos internals and `*FINAL*` files. Use the scoped `assets` command.
- Treating the audit as a malware *scanner* — it reviews persistence points; recommend a real scanner for certainty.
- Deleting Messages expecting local-only effect while Messages-in-iCloud is ON. It syncs everywhere.
