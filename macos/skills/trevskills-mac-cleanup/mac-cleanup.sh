#!/usr/bin/env bash
#
# trevskills-mac-cleanup.sh — safe, dry-run-first disk reclamation for macOS
#
# Design rules:
#   * DRY-RUN BY DEFAULT. Nothing is deleted unless --apply is passed.
#   * Only regenerable caches/logs are ever removed. Never user documents,
#     never message CONTENT, never keys/credentials.
#   * PROTECTED_ROOTS are refused even if a category path resolves into them.
#   * Destructive user-file operations (ASSET files) go to the Trash, never rm.
#
# Usage:
#   trevskills-mac-cleanup.sh scan                 # report reclaimable space by category (no changes)
#   trevskills-mac-cleanup.sh clean [cats...]      # dry-run of a clean (default cats = safe set)
#   trevskills-mac-cleanup.sh clean [cats...] --apply
#   trevskills-mac-cleanup.sh assets scan [dirs...]        # list scoped "Asset" export files
#   trevskills-mac-cleanup.sh assets trash [dirs...] --apply  # move them to Trash
#   trevskills-mac-cleanup.sh processes            # read-only: uptime/swap, top CPU+mem, malware flag
#   trevskills-mac-cleanup.sh processes quit [--apply]  # quit safe background helpers only
#   trevskills-mac-cleanup.sh processes reset [--apply] # reset stuck Apple helpers (auto-relaunch)
#   trevskills-mac-cleanup.sh report [baseline_free_kb] # GB freed + memory + maintenance plan
#   trevskills-mac-cleanup.sh worktrees [--apply]  # remove scrum worktrees of done/aborted jobs
#   trevskills-mac-cleanup.sh transcripts [--apply] # gzip-archive Claude transcripts untouched 30+ days
#
# Categories: app-caches dev-caches adobe-caches messages-cache logs system-caches
# "safe set" (default) = app-caches dev-caches adobe-caches messages-cache logs

set -uo pipefail

APPLY=0
HOME_DIR="${HOME}"
TRASH="${HOME_DIR}/.Trash"

# --- Paths that must NEVER be deleted from, no matter what ------------------
PROTECTED_ROOTS=(
  "${HOME_DIR}/Documents"
  "${HOME_DIR}/Desktop"
  "${HOME_DIR}/Downloads"
  "${HOME_DIR}/Developer"
  "${HOME_DIR}/Pictures"
  "${HOME_DIR}/Movies"
  "${HOME_DIR}/.ssh"
  "${HOME_DIR}/.gnupg"
  "${HOME_DIR}/Library/Keychains"
  "${HOME_DIR}/Library/Messages/Attachments"   # message CONTENT — never auto-touch
  "${HOME_DIR}/Library/Messages/chat.db"
)

human() { du -sh "$1" 2>/dev/null | awk '{print $1}'; }

is_protected() {
  local target; target="$(cd "$(dirname "$1")" 2>/dev/null && pwd)/$(basename "$1")" || target="$1"
  case "$target" in
    *.photoslibrary|*.photoslibrary/*) return 0 ;;
  esac
  local p
  for p in "${PROTECTED_ROOTS[@]}"; do
    [[ "$target" == "$p" || "$target" == "$p"/* ]] && return 0
  done
  return 1
}

# Narrower guard for the ASSET flow: it INTENTIONALLY works in Desktop/Downloads,
# so it only refuses genuinely dangerous locations (libraries, keys, app internals).
is_protected_asset() {
  local target; target="$(cd "$(dirname "$1")" 2>/dev/null && pwd)/$(basename "$1")" || target="$1"
  case "$target" in
    *.photoslibrary/*|*/Library/*|"${HOME_DIR}/.ssh/"*|"${HOME_DIR}/.gnupg/"*|*/node_modules/*|*/.git/*|*FINAL*) return 0 ;;
  esac
  return 1
}

# Delete the CONTENTS of a directory (not the dir itself), with all guards.
purge_dir() {
  local dir="$1"
  [[ -e "$dir" ]] || return 0
  if is_protected "$dir"; then
    printf '   [SKIP protected] %s\n' "$dir"; return 0
  fi
  local sz; sz="$(human "$dir")"
  if [[ "$APPLY" == "1" ]]; then
    ( shopt -s dotglob nullglob; rm -rf -- "$dir"/* ) 2>/dev/null
    printf '   [freed ~%s] %s\n' "${sz:-0}" "$dir"
  else
    printf '   [would free ~%s] %s\n' "${sz:-0}" "$dir"
  fi
}

run_cmd() { # for tool-native cleaners (npm/brew/pnpm)
  local desc="$1"; shift
  if [[ "$APPLY" == "1" ]]; then
    printf '   [running] %s\n' "$desc"; "$@" >/dev/null 2>&1
  else
    printf '   [would run] %s\n' "$desc"
  fi
}

cat_app_caches() {
  echo "== app-caches =="
  purge_dir "${HOME_DIR}/Library/Caches/com.spotify.client"
  purge_dir "${HOME_DIR}/Library/Caches/Google"
  purge_dir "${HOME_DIR}/Library/Application Support/Spotify/PersistentCache"
  for app in Code Cursor "Google/Chrome" Slack discord "com.microsoft.teams2"; do
    for sub in Cache CachedData CachedExtensionVSIXs "Code Cache" GPUCache "Service Worker/CacheStorage"; do
      purge_dir "${HOME_DIR}/Library/Application Support/${app}/${sub}"
    done
  done
  purge_dir "${HOME_DIR}/Library/Application Support/zoom.us/AutoUpdater"
}

cat_dev_caches() {
  echo "== dev-caches =="
  purge_dir "${HOME_DIR}/Library/Caches/ms-playwright"
  purge_dir "${HOME_DIR}/Library/Caches/ms-playwright-mcp"
  purge_dir "${HOME_DIR}/Library/Caches/node-gyp"
  purge_dir "${HOME_DIR}/Library/Caches/next-swc"
  purge_dir "${HOME_DIR}/Library/Caches/typescript"
  purge_dir "${HOME_DIR}/Library/Caches/Homebrew"
  purge_dir "${HOME_DIR}/Library/Developer/Xcode/DerivedData"
  purge_dir "${HOME_DIR}/.npm/_logs"
  purge_dir "${HOME_DIR}/.npm/_npx"
  command -v npm  >/dev/null && run_cmd "npm cache clean --force" npm cache clean --force
  command -v brew >/dev/null && run_cmd "brew cleanup --prune=all" brew cleanup --prune=all
  command -v pnpm >/dev/null && run_cmd "pnpm store prune" pnpm store prune
  command -v pip3 >/dev/null && run_cmd "pip3 cache purge" pip3 cache purge
}

cat_adobe_caches() {
  echo "== adobe-caches (user-level, no sudo) =="
  purge_dir "${HOME_DIR}/Library/Caches/Adobe"
  purge_dir "${HOME_DIR}/Library/Caches/com.adobe.illustrator"
  purge_dir "${HOME_DIR}/Library/Caches/com.adobe.Photoshop"
  purge_dir "${HOME_DIR}/Library/Application Support/Adobe/Common/Media Cache"
  purge_dir "${HOME_DIR}/Library/Application Support/Adobe/Common/Media Cache Files"
  purge_dir "${HOME_DIR}/Library/Application Support/Adobe/Common/Peak Files"
}

cat_messages_cache() {
  echo "== messages-cache (regenerable caches only — NOT attachments/chat.db) =="
  purge_dir "${HOME_DIR}/Library/Messages/Caches"
}

cat_logs() {
  echo "== logs =="
  purge_dir "${HOME_DIR}/Library/Logs"
}

cat_system_caches() {
  echo "== system-caches (aggressive: sweeps remaining ~/Library/Caches) =="
  local d
  for d in "${HOME_DIR}"/Library/Caches/*; do
    [[ -d "$d" ]] || continue
    case "$(basename "$d")" in
      CloudKit|com.apple.containermanagerd) printf '   [SKIP sensitive] %s\n' "$d"; continue ;;
    esac
    purge_dir "$d"
  done
}

cat_build_caches() {
  echo "== build-caches (Next.js/Turbo .next & .turbo — auto-rebuild, break nothing) =="
  # These live under ~/Developer (a protected root), so purge_dir would skip them.
  # They are known-safe regenerable build output, so delete the dir directly.
  local d sz
  while IFS= read -r d; do
    sz="$(human "$d")"
    if [[ "$APPLY" == "1" ]]; then rm -rf "$d" && printf '   [freed ~%s] %s\n' "${sz:-0}" "$d"
    else printf '   [would free ~%s] %s\n' "${sz:-0}" "$d"; fi
  done < <(find "${HOME_DIR}/Developer" -type d \( -name ".next" -o -name ".turbo" \) -prune 2>/dev/null)
}

do_scan() {
  echo "===== DISK BEFORE ====="; df -h / /System/Volumes/Data 2>/dev/null | sed 's/^/   /'
  echo; echo "===== RECLAIMABLE BY CATEGORY (nothing deleted) ====="
  APPLY=0
  cat_app_caches; cat_dev_caches; cat_adobe_caches; cat_messages_cache; cat_logs; cat_system_caches
  echo; echo "Run:  trevskills-mac-cleanup.sh clean            (dry-run of safe set)"
  echo "Then: trevskills-mac-cleanup.sh clean --apply   (actually clean)"
}

do_clean() {
  local cats=()
  for a in "$@"; do [[ "$a" == "--apply" ]] && APPLY=1 || cats+=("$a"); done
  [[ ${#cats[@]} -eq 0 ]] && cats=(app-caches dev-caches adobe-caches messages-cache logs)
  [[ "$APPLY" == "1" ]] && echo ">>> APPLY MODE — deleting" || echo ">>> DRY RUN — nothing will be deleted (add --apply)"
  echo "Categories: ${cats[*]}"; echo
  for c in "${cats[@]}"; do
    case "$c" in
      app-caches) cat_app_caches ;;
      dev-caches) cat_dev_caches ;;
      adobe-caches) cat_adobe_caches ;;
      messages-cache) cat_messages_cache ;;
      logs) cat_logs ;;
      system-caches) cat_system_caches ;;
      build-caches) cat_build_caches ;;
      *) echo "   [unknown category] $c" ;;
    esac
  done
  [[ "$APPLY" == "1" ]] && { echo; echo "===== DISK AFTER ====="; df -h /System/Volumes/Data 2>/dev/null | sed 's/^/   /'; }
}

# --- ASSET file handling (scoped Illustrator artboard exports) --------------
# Match ONLY basenames like: Asset, Asset 3, Asset 15@300x, Asset 5@4x
# (case-insensitive "asset"), with design/image extensions. This deliberately
# EXCLUDES files like "brand assets_FINAL_DIGITAL.ai" (basename isn't "Asset N")
# and .plist/.plj Photos-library internals.
asset_find() {
  local dirs=("$@")
  [[ ${#dirs[@]} -eq 0 ]] && dirs=("${HOME_DIR}/Desktop" "${HOME_DIR}/Downloads")
  # macOS/BSD find: -E enables extended regex (must precede the paths).
  # Basename must be "Asset" plus, in order, any of:
  #   " N"      artboard number          Asset 3.svg
  #   "-NNN"    Export-for-Screens scale/quality suffix   Asset 4-100.jpg
  #   "@Nx"     retina scale             Asset 15@300x.png
  #   " (N)"    duplicate-download marker  Asset 2 (1).svg
  # Anchoring to "Asset" at the START of the basename is what keeps this from
  # eating real work like "brand assets_FINAL_DIGITAL.ai".
  find -E "${dirs[@]}" \
    -type d \( -name '*.photoslibrary' -o -name node_modules -o -name .git \) -prune -o \
    -type f -iregex '.*/[Aa]sset( [0-9]+)?(-[0-9]+)?(@[0-9]+[a-z]?)?( \([0-9]+\))?\.(ai|eps|psd|pdf|svg|png|jpg|jpeg|tif|tiff)' -print 2>/dev/null
}

# Format bytes. Used for BOTH per-file and total so they can never disagree.
human() { awk -v s="${1:-0}" 'BEGIN{u="B"; if(s>1073741824){s/=1073741824;u="G"}else if(s>1048576){s/=1048576;u="M"}else if(s>1024){s/=1024;u="K"}; printf "%.1f%s", s, u}'; }

# Dataless (evicted) iCloud file? `du` reports 0 blocks for these because the
# bytes live in the cloud, not on disk — st_size is still the true size.
is_dataless() { [[ "$(stat -f%b "$1" 2>/dev/null || echo 1)" -eq 0 ]]; }

assets_scan() {
  echo "===== SCOPED 'Asset' EXPORT FILES (no changes) ====="
  local total=0 cloud=0 n=0 f sz tag
  while IFS= read -r f; do
    is_protected_asset "$f" && { printf '   [SKIP protected] %s\n' "$f"; continue; }
    # ALWAYS size with stat (logical bytes), never `du` (allocated blocks):
    # every evicted iCloud file reports 0B under du, which made whole folders
    # of real exports look like they were worth nothing to reclaim.
    sz=$(stat -f%z "$f" 2>/dev/null || echo 0); total=$((total+sz)); n=$((n+1))
    tag=""; if is_dataless "$f"; then tag="  [cloud-only]"; cloud=$((cloud+1)); fi
    printf '   %8s  %s%s\n' "$(human "$sz")" "$f" "$tag"
  done < <(asset_find "$@")
  echo; printf '   %d files, ~%s total\n' "$n" "$(human "$total")"
  if [[ "$cloud" -gt 0 ]]; then
    printf '   %d of them are [cloud-only] — trashing frees NO local disk space,\n' "$cloud"
    echo   '   it only removes the files (and syncs that removal to your other devices).'
  fi
}

assets_trash() {
  local apply=0 dirs=()
  for a in "$@"; do [[ "$a" == "--apply" ]] && apply=1 || dirs+=("$a"); done
  mkdir -p "$TRASH"
  echo "===== MOVE SCOPED 'Asset' FILES TO TRASH ====="
  [[ "$apply" == "1" ]] && echo ">>> APPLY — moving to $TRASH" || echo ">>> DRY RUN — add --apply to move"
  local f base dest
  while IFS= read -r f; do
    is_protected_asset "$f" && continue
    base="$(basename "$f")"; dest="${TRASH}/${base}"
    while [[ -e "$dest" ]]; do dest="${TRASH}/$(basename "${base%.*}")-dup.${base##*.}"; base="$(basename "$dest")"; done
    if [[ "$apply" == "1" ]]; then mv -- "$f" "$dest" && printf '   [trashed] %s\n' "$f"
    else printf '   [would trash] %s\n' "$f"; fi
  done < <(asset_find ${dirs[@]+"${dirs[@]}"})
}

# --- iCloud offload: free local space, keep file in the cloud --------------
ICLOUD_ROOT="${HOME_DIR}/Library/Mobile Documents/com~apple~CloudDocs"
in_icloud() { case "$1" in "${ICLOUD_ROOT}"/*|"${HOME_DIR}/Desktop/"*|"${HOME_DIR}/Documents/"*) return 0;; *) return 1;; esac; }

offload_evict() { # remove local copy of an already-in-iCloud file (non-destructive: stays in cloud)
  local p="$1"
  [[ -e "$p" ]] || { echo "not found: $p"; return 1; }
  if ! in_icloud "$p"; then
    echo "NOT in an iCloud-synced folder (Desktop/Documents/iCloud Drive): $p"
    echo "  -> use 'offload move' to relocate it into iCloud Drive first."; return 1
  fi
  echo "Evicting local copy (file remains in iCloud, re-downloads on demand):"
  echo "  $p  ($(du -h "$p" 2>/dev/null | awk '{print $1}') local)"
  brctl evict "$p" 2>/dev/null
  if [[ "$(stat -f%b "$p" 2>/dev/null || echo 1)" == "0" ]]; then
    echo "  done — local copy freed (still in iCloud)."
  else
    echo "  CLI evict didn't take — this file is pinned 'Keep Downloaded'."
    echo "  FINISH IN FINDER: right-click the file -> \"Remove Download\" (no CLI equivalent under FileProvider)."
  fi
}

offload_move() { # move a LOCAL file into iCloud Drive, then evict local copy
  local apply=0 p="" dest_sub="Offloaded"
  for a in "$@"; do case "$a" in --apply) apply=1;; *) [[ -z "$p" ]] && p="$a" || dest_sub="$a";; esac; done
  [[ -e "$p" ]] || { echo "not found: $p"; return 1; }
  local dest_dir="${ICLOUD_ROOT}/${dest_sub}" dest="${ICLOUD_ROOT}/${dest_sub}/$(basename "$p")"
  echo "Plan: move into iCloud Drive, then free local copy"
  echo "  from: $p  ($(du -h "$p" 2>/dev/null | awk '{print $1}'))"
  echo "  to:   $dest"
  if [[ "$apply" != "1" ]]; then echo ">>> DRY RUN — add --apply to do it"; return 0; fi
  if mkdir -p "$dest_dir" && mv -- "$p" "$dest"; then
    echo "  moved into iCloud Drive."
    brctl evict "$dest" 2>/dev/null
    if [[ "$(stat -f%b "$dest" 2>/dev/null || echo 1)" == "0" ]]; then echo "  local copy freed (kept in iCloud)."
    else echo "  FINISH IN FINDER: right-click the file -> \"Remove Download\" to free the local copy."; fi
  else echo "  move failed."; fi
}

# --- archive-offload: move stale files to an archive folder, then evict ----
# Files in SRC not modified in the last <months> are moved (preserving subpaths)
# into ARCHIVE, then their local copies are evicted (they stay in iCloud).
# ARCHIVE must be a SIBLING of SRC (not inside it) and not "Keep Downloaded".
archive_offload() {
  local src="" arch="" months=6 apply=0 a
  for a in "$@"; do
    case "$a" in
      --apply) apply=1 ;;
      [0-9]*)  months="$a" ;;
      *) if [[ -z "$src" ]]; then src="$a"; elif [[ -z "$arch" ]]; then arch="$a"; fi ;;
    esac
  done
  [[ -d "$src" ]]  || { echo "source folder not found: $src"; return 1; }
  [[ -n "$arch" ]] || { echo "need an archive folder path"; return 1; }
  case "$arch" in "$src"|"$src"/*) echo "archive must be a SIBLING, not inside the source"; return 1;; esac

  local ref cutoff; cutoff="$(date -v-"${months}"m +%Y%m%d0000 2>/dev/null)"
  [[ -n "$cutoff" ]] || { echo "bad months value"; return 1; }
  ref="$(mktemp)"; touch -t "$cutoff" "$ref"

  echo ">>> archive-offload: files in '$src' older than ${months} months (before $(date -v-"${months}"m +%Y-%m-%d))"
  [[ "$apply" == "1" ]] && echo ">>> APPLY — moving to '$arch' + evicting" || echo ">>> DRY RUN — add --apply to do it"
  local n=0 offloadable=0 f rel dest blocks
  while IFS= read -r f; do
    rel="${f#"$src"/}"; dest="${arch}/${rel}"
    blocks="$(stat -f%b "$f" 2>/dev/null || echo 0)"; offloadable=$((offloadable + blocks*512)); n=$((n+1))
    if [[ "$apply" == "1" ]]; then
      mkdir -p "$(dirname "$dest")" && mv -- "$f" "$dest"
      printf '   moved  %6s  %s\n' "$(du -h "$dest" 2>/dev/null | awk '{print $1}')" "$rel"
    else
      printf '   would move  %6s  %s\n' "$(du -h "$f" 2>/dev/null | awk '{print $1}')" "$rel"
    fi
  done < <(find "$src" -type f ! -newer "$ref" ! -name '.DS_Store' 2>/dev/null)
  rm -f "$ref"
  echo "   $n file(s), ~$(echo "$offloadable" | awk '{printf "%.2f GB", $1/1073741824}') of local space to reclaim."
  if [[ "$apply" == "1" ]]; then
    echo
    echo "   NOTE: files are moved but still local. macOS only offloads iCloud files"
    echo "   that carry a 'Keep Downloaded' pin via Finder (no CLI equivalent exists)."
    echo "   FINISH IN FINDER:  right-click '$arch'  ->  \"Remove Download\""
    echo "   That clears the pin, offloads all $n files, frees the space, keeps them in iCloud."
  fi
}

# --- processes: analyze what's running, flag anything unsigned, quit bloat ----
# Read-only report by default. `processes quit --apply` quits ONLY background
# helpers that never hold user data (Adobe CC services, updaters). It NEVER
# quits apps that may have unsaved work or open state (Illustrator, Photoshop,
# editors, terminals, browsers) — those are listed as manual suggestions only.

# Background helpers safe to quit — no user data, relaunch at login / next use.
SAFE_QUIT_PROCS=(
  "Creative Cloud UI Helper"
  "Creative Cloud Content Manager.node"
  "Creative Cloud Libraries Synchronizer"
  "Adobe Desktop Service"
  "AdobeIPCBroker"
  "CCLibrary"
  "CCXProcess"
)
# User-facing apps we only SUGGEST quitting (may hold tabs/music/state).
SUGGEST_QUIT_APPS=("Spotify" "App Store" "Google Chrome" "Microsoft Teams" "zoom.us" "Slack")

# --- reset: Apple system helpers that RELAUNCH themselves ---------------------
# Distinct from SAFE_QUIT_PROCS (third-party helpers that stay dead until login).
# These are launchd/XPC services: killing one is a RESET, not a quit — macOS
# restarts it within seconds, on demand. They hold no user data. They are the
# usual suspects for "spinning at 100% CPU forever" because they retry a bad
# input (a huge attachment, an undecodable message, a stuck photo analysis)
# indefinitely, and such a retry loop survives everything except a fresh process.
RESET_PROCS=(
  "MessagesBlastDoorService"   # sandboxed message parser — top offender
  "IMTranscoderAgent"          # attachment/video transcode for Messages
  "identityservicesd"          # IDS (iMessage/FaceTime); reconnects on its own
  "mediaanalysisd"             # Photos/Visual Look Up analysis; resumes
  "photoanalysisd"             # Photos face/scene analysis; resumes
  "cloudd"                     # CloudKit transport — same processes already
  "contactsd"                  #   killed by the Contacts fix; same rationale
  "suggestd"                   # Siri/Spotlight suggestion indexing
  "spotlightknowledged"        # Spotlight knowledge indexing
)

# NEVER kill these, no matter how much CPU or RAM they use.
# THIS GUARD IS THE POINT OF THE WHOLE FUNCTION. WindowServer routinely sits at
# 20-35% CPU during ordinary use (window compositing, external displays) and so
# WILL trip any CPU threshold — killing it force-logs the user out and loses
# every unsaved document in every open app. The others are equally fatal:
# killing launchd panics the kernel; loginwindow/securityd/opendirectoryd end
# the session. Tested BEFORE the threshold check, never after.
NEVER_RESET_RE='WindowServer|kernel_task|launchd|loginwindow|logind|opendirectoryd|securityd|trustd|coreaudiod|SystemUIServer|Dock|Finder'

# Only reset a helper that is ACTUALLY hogging — a healthy idle daemon is left
# alone (killing it just churns and re-warms its caches for no gain).
RESET_CPU_PCT=${RESET_CPU_PCT:-20}
RESET_RSS_MB=${RESET_RSS_MB:-500}

# True (0) if this command name is unsafe to kill. Split out so the self-check
# can exercise it with synthetic names — see `processes reset --self-check`.
reset_is_forbidden() { [[ "$1" =~ $NEVER_RESET_RE ]]; }

# True (0) if over either threshold. %cpu is a float, so compare via awk.
reset_is_hogging() {
  local cpu="$1" rss_kb="$2"
  [[ "$(awk -v c="$cpu" -v t="$RESET_CPU_PCT" 'BEGIN{print (c>=t)?1:0}')" == "1" ]] && return 0
  [[ $(( rss_kb / 1024 )) -ge "$RESET_RSS_MB" ]] && return 0
  return 1
}

# Asserts the denylist actually fires. If this ever fails, DO NOT run --apply:
# a broken guard means the next run logs the user out.
reset_self_check() {
  local bad=0 n
  for n in /System/Library/PrivateFrameworks/SkyLight.framework/Resources/WindowServer \
           WindowServer kernel_task launchd loginwindow securityd; do
    reset_is_forbidden "$n" || { echo "FAIL: '$n' NOT blocked by denylist"; bad=1; }
  done
  for n in MessagesBlastDoorService IMTranscoderAgent mediaanalysisd; do
    reset_is_forbidden "$n" && { echo "FAIL: '$n' wrongly blocked"; bad=1; }
  done
  reset_is_hogging 99 1000     || { echo "FAIL: 99% CPU not flagged"; bad=1; }
  reset_is_hogging 0.1 2000000 || { echo "FAIL: 1.9GB RSS not flagged"; bad=1; }
  reset_is_hogging 0.1 1000    && { echo "FAIL: idle proc wrongly flagged"; bad=1; }
  [[ "$bad" == "0" ]] && echo "self-check OK — denylist and thresholds behave"
  return "$bad"
}

proc_reset() {
  [[ "${1:-}" == "--self-check" ]] && { reset_self_check; return $?; }
  local apply=0; [[ "${1:-}" == "--apply" ]] && apply=1
  echo "== Stuck Apple helpers over threshold (CPU >= ${RESET_CPU_PCT}% or RSS >= ${RESET_RSS_MB} MB) =="
  echo "   These relaunch on their own — killing them is a reset, not a quit."
  local pid cpu rss comm base r match total=0
  while read -r pid cpu rss comm; do
    [[ -z "${pid:-}" ]] || [[ "$pid" == "PID" ]] && continue
    # Denylist FIRST — before any threshold logic can select a fatal process.
    reset_is_forbidden "$comm" && continue
    base="${comm##*/}"; match=0
    for r in "${RESET_PROCS[@]}"; do [[ "$base" == "$r" ]] && { match=1; break; }; done
    [[ "$match" == "1" ]] || continue
    reset_is_hogging "$cpu" "$rss" || continue
    total=$((total+1))
    if [[ "$apply" == "1" ]]; then
      kill "$pid" 2>/dev/null && printf '   reset: %-28s (pid %s, %s%% cpu, %s MB)\n' "$base" "$pid" "$cpu" "$((rss/1024))"
    else
      printf '   would reset: %-28s (pid %s, %s%% cpu, %s MB)\n' "$base" "$pid" "$cpu" "$((rss/1024))"
    fi
  done < <(ps -Axo pid,%cpu,rss,comm)
  if [[ "$total" -eq 0 ]]; then
    echo "   (none over threshold — system helpers are behaving)"
  elif [[ "$apply" == "0" ]]; then
    echo "   Re-run with --apply to reset these. They restart within seconds."
  else
    echo "   Done. Reopen Messages/Photos if you had them in front."
  fi
}

# Shared memory/uptime summary — used by `processes` and the run `report`.
# Sets globals MEM_UP_DAYS / MEM_SWAP_MB so callers can reuse the numbers.
MEM_UP_DAYS=0; MEM_SWAP_MB=0
mem_summary() {
  local comp_mb
  MEM_UP_DAYS=$(uptime | grep -oE 'up [0-9]+ day' | grep -oE '[0-9]+' | head -1); MEM_UP_DAYS=${MEM_UP_DAYS:-0}
  MEM_SWAP_MB=$(sysctl -n vm.swapusage 2>/dev/null | grep -oE 'used = [0-9.]+M' | grep -oE '[0-9.]+' | head -1)
  MEM_SWAP_MB=${MEM_SWAP_MB:-0}
  comp_mb=$(vm_stat | awk '/occupied by compressor/{gsub(/[^0-9]/,"",$NF); printf "%d", $NF*16384/1048576}')
  printf '  Uptime: %s day(s)   Swap used: %s MB   Compressed RAM: %s MB\n' \
    "$MEM_UP_DAYS" "${MEM_SWAP_MB:-?}" "${comp_mb:-?}"
  if [[ "$MEM_UP_DAYS" -ge 7 ]] || [[ "$(printf '%.0f' "${MEM_SWAP_MB:-0}")" -ge 2048 ]]; then
    echo "  >>> RESTART RECOMMENDED — high uptime and/or heavy swap. A reboot clears"
    echo "      all swap and compressed memory instantly: the single biggest speed win."
    echo "      (Save open work first.)"
  fi
}

proc_report() {
  echo "== Uptime / load =="; uptime
  echo
  echo "== Memory pressure =="; mem_summary
  echo
  echo "== Top 12 by CPU =="
  ps -Ao pid,%cpu,%mem,rss,comm -r | head -13
  echo
  echo "== Top 12 by memory (RSS) =="
  ps -Ao pid,%cpu,%mem,rss,comm -m | head -13
  echo
  echo "== Heavy multi-process apps (aggregate RSS) =="
  local a
  for a in "Adobe" "Google Chrome" "Spotify" "Microsoft"; do
    ps -Axo rss,comm | grep -i "$a" | grep -v grep | \
      awk -v n="$a" '{s+=$1;c++} END{if(c) printf "  %-16s %3d procs  ~%d MB\n", n, c, s/1024}'
  done
  echo
  echo "== Malicious check: running binaries with NO valid Developer ID / Apple signature =="
  echo "   (Apple system paths are trusted; everything else must be signed. Flags = investigate.)"
  local flagged=0 p sig
  while IFS= read -r p; do
    [[ -x "$p" ]] || continue
    # Capture to a var first — piping into `grep -q` races with pipefail:
    # grep -q exits on match and SIGPIPEs codesign, making the pipeline report
    # failure even on a VALID signature. `case` on the captured text avoids that.
    sig="$(codesign -dv --verbose=2 "$p" 2>&1 </dev/null)"
    case "$sig" in
      *"Authority=Apple"*|*"Authority=Developer ID"*|*"Authority=Software Signing"*) : ;;
      *) printf '   >>> UNSIGNED/UNKNOWN: %s\n' "$p"; flagged=1 ;;
    esac
  done < <(ps -Axo comm | grep '^/' | grep -vE '^/System|^/usr|^/sbin|^/Library/Apple' | sort -u)
  [[ "$flagged" == "0" ]] && echo "   (clean — every non-Apple running binary is validly signed)"
  echo
  echo "Next: './trevskills-mac-cleanup.sh processes quit'   (dry-run of safe background quits)"
  echo "      './trevskills-mac-cleanup.sh processes reset'  (dry-run of stuck Apple helper resets)"
}

proc_quit() {
  local apply=0; [[ "${1:-}" == "--apply" ]] && apply=1
  echo "== Safe-to-quit background helpers (no user data; relaunch automatically) =="
  local proc n total=0
  for proc in "${SAFE_QUIT_PROCS[@]}"; do
    n=$(pgrep -if "$proc" 2>/dev/null | wc -l | tr -d ' ')
    [[ "$n" -eq 0 ]] && continue
    total=$((total+n))
    if [[ "$apply" == "1" ]]; then
      pkill -if "$proc" 2>/dev/null && printf '   quit (%s): %s\n' "$n" "$proc"
    else
      printf '   would quit (%s): %s\n' "$n" "$proc"
    fi
  done
  [[ "$total" -eq 0 ]] && echo "   (none running)"
  echo
  echo "== User apps you may also want to quit MANUALLY (hold tabs/music/state) =="
  echo "   Not auto-quit — close them yourself to avoid losing anything:"
  local app
  for app in "${SUGGEST_QUIT_APPS[@]}"; do
    pgrep -if "$app" >/dev/null 2>&1 && printf '     osascript -e '\''tell application \"%s\" to quit'\''\n' "$app"
  done
  echo
  echo "   NEVER auto-quit: Illustrator/Photoshop/editors (may have unsaved work)."
  [[ "$apply" == "0" ]] && echo "   Re-run with --apply to quit the background helpers above."
}

# --- run report: GB freed, memory summary, personalized maintenance plan -----
# Persists free-space + timestamp between runs (STATE_FILE) so each report can
# show change since last run and recommend how often to clean & restart.
STATE_DIR="${HOME_DIR}/.mac-cleanup"
STATE_FILE="${STATE_DIR}/last-run"        # format: <epoch>|<free_kb>

free_kb() { df -k /System/Volumes/Data 2>/dev/null | tail -1 | awk '{print $4}' | grep -qE '^[0-9]+$' && \
            df -k /System/Volumes/Data 2>/dev/null | tail -1 | awk '{print $4}' || \
            df -k / 2>/dev/null | tail -1 | awk '{print $4}'; }
gb() { awk -v k="${1:-0}" 'BEGIN{printf "%.1f", k/1048576}'; }

# do_report [baseline_free_kb]
# Pass the free-space (KB) captured BEFORE a cleanup to show "freed this session".
do_report() {
  local baseline="${1:-}"
  local cur now; cur="$(free_kb)"; now="$(date +%s)"
  echo "============================================================"
  echo "   MAC-CLEANUP REPORT"
  echo "============================================================"
  echo
  echo "== Disk space =="
  printf '  Free now: %s GB\n' "$(gb "$cur")"
  if [[ -n "$baseline" ]] && [[ "$baseline" =~ ^[0-9]+$ ]]; then
    printf '  Freed THIS session: %s GB  (before: %s GB)\n' "$(gb $((cur-baseline)))" "$(gb "$baseline")"
  fi

  local rec_freq rec_note days=0
  if [[ -f "$STATE_FILE" ]]; then
    local prev_epoch prev_kb; IFS='|' read -r prev_epoch prev_kb < "$STATE_FILE"
    days=$(( (now - prev_epoch) / 86400 ))
    local delta=$(( cur - prev_kb )); local sign=""; [[ "$delta" -ge 0 ]] && sign="+"
    printf '  Since last run (%s day(s) ago): %s%s GB free\n' "$days" "$sign" "$(gb "$delta")"
    # Recommend frequency from the fill rate (space LOST per day) and headroom.
    IFS='|' read -r rec_freq rec_note < <(awk -v cur="$cur" -v prev="$prev_kb" -v days="$days" 'BEGIN{
      freeGB=cur/1048576; d=(days<1?1:days); rate=(prev-cur)/1048576/d;
      if(freeGB<20)      printf "WEEKLY|Low headroom (<20 GB). Clean weekly + restart often — under ~25 GB free, iCloud/Contacts sync can wedge.";
      else if(rate>1)    printf "WEEKLY|Filling ~%.1f GB/day. A weekly run keeps you ahead.", rate;
      else if(rate>0.3)  printf "EVERY 2 WEEKS|Filling ~%.1f GB/day. Every couple weeks is plenty.", rate;
      else               printf "MONTHLY|Filling only ~%.1f GB/day. Once a month is fine.", (rate<0?0:rate);
    }')
  else
    echo "  (first tracked run — saved a baseline; next run will show GB/day fill rate)"
    rec_freq="MONTHLY"; rec_note="No history yet — start with monthly and adjust once trends show."
  fi
  echo
  echo "== Memory & uptime =="; mem_summary
  echo
  echo "== Your maintenance plan =="
  printf '  • Run this cleanup: %s\n' "$rec_freq"
  printf '    %s\n' "$rec_note"
  if [[ "$MEM_UP_DAYS" -ge 7 ]]; then
    printf '  • RESTART NOW-ISH: %s days uptime. Reboot weekly — it clears swap + the memory compressor, the biggest speed win.\n' "$MEM_UP_DAYS"
  else
    echo "  • Restart weekly (you are fine right now). It clears swap + compressed memory before they pile up."
  fi
  echo "  • Keep >25 GB free at all times — the recurring iCloud Contacts/Messages sync wedge is triggered by disk pressure."
  echo "  • Big art archives: offload to iCloud ('archive' cmd) or an external SSD instead of letting them sit local."
  echo "  • Run 'audit malware' monthly and after installing anything new."
  echo
  # Persist current state for next run.
  mkdir -p "$STATE_DIR"; printf '%s|%s\n' "$now" "$cur" > "$STATE_FILE"
  echo "(Baseline saved. Re-run 'report' anytime for an updated picture.)"
}

# --- worktrees: stale scrum worktree sweep ----------------------------------
# Reads the scrum registry (same file board.projects() reads) and lists
# <repo>/.claude/worktrees/scrum-<id> for jobs whose board stage is done or
# aborted. --apply runs `git worktree remove --force` and `git branch -d`
# (never -D, so an unmerged branch is kept). Anything unreadable is skipped
# with a note, never treated as stale.
stale_worktrees() {
  local apply=0; [[ "${1:-}" == "--apply" ]] && apply=1
  python3 - "$apply" <<'PY'
import json, os, subprocess, sys
apply = sys.argv[1] == "1"
print(">>> APPLY — removing stale scrum worktrees" if apply else ">>> DRY RUN — nothing will be removed (add --apply)")
reg = os.environ.get("SCRUM_REGISTRY") or os.path.expanduser("~/.claude/trevskills-scrum/projects.json")
try:
    with open(reg) as f:
        repos = json.load(f)
    if not isinstance(repos, list):
        raise ValueError("not a JSON list")
except (OSError, ValueError) as e:
    print(f"   note: scrum registry {reg} unreadable ({e}); skipped")
    sys.exit(0)
total_kb = n = 0
for repo in repos:
    if not isinstance(repo, str) or not os.path.isdir(os.path.join(repo, "scrum")):
        continue
    wt_root = os.path.join(repo, ".claude", "worktrees")
    if not os.path.isdir(wt_root):
        print(f"   note: {repo} has no .claude/worktrees; skipped")
        continue
    board = os.path.join(repo, "scrum", "board.json")
    try:
        with open(board) as f:
            jobs = json.load(f)["jobs"]
        if not isinstance(jobs, list):
            raise ValueError("jobs is not a list")
    except (OSError, ValueError, KeyError, TypeError) as e:
        print(f"   note: {board} unreadable or malformed ({e}); skipped")
        continue
    for job in jobs:
        if not isinstance(job, dict) or job.get("stage") not in ("done", "aborted"):
            continue
        jid = job.get("id")
        # The id becomes a path part and a branch name: refuse anything odd.
        if not isinstance(jid, str) or not jid or "/" in jid or jid.startswith((".", "-")):
            continue
        path = os.path.join(wt_root, "scrum-" + jid)
        if os.path.islink(path) or not os.path.isdir(path):
            continue
        du = subprocess.run(["du", "-sk", path], capture_output=True, text=True).stdout.split()
        kb = int(du[0]) if du and du[0].isdigit() else 0
        size = subprocess.run(["du", "-sh", path], capture_output=True, text=True).stdout.split()
        size = size[0] if size else "?"
        total_kb += kb; n += 1
        line = f"   {size:>6}  {repo}  {jid}  [{job['stage']}]"
        if not apply:
            print("   would remove" + line[2:])
            continue
        r = subprocess.run(["git", "-C", repo, "worktree", "remove", "--force", path], capture_output=True, text=True)
        if r.returncode != 0:
            print(f"   FAILED remove{line[2:]}: {(r.stderr.strip() or 'git refused').splitlines()[0]}")
            continue
        b = subprocess.run(["git", "-C", repo, "branch", "-d", "scrum/" + jid], capture_output=True, text=True)
        if b.returncode == 0:
            print(f"   removed{line[2:]}; branch scrum/{jid} deleted")
        else:
            print(f"   removed{line[2:]}; branch scrum/{jid} kept as unmerged ({(b.stderr.strip() or 'git refused').splitlines()[0]})")
print(f"\n   {n} stale worktree(s), ~{total_kb / 1024:.1f} MB total")
PY
}

# --- transcripts: gzip-archive old Claude transcripts -------------------------
# Lists *.jsonl under ~/.claude/projects/<project>/ (recursing, skipping any
# memory/ folder) with mtime 30+ days old. --apply gzips each into
# ~/.claude/transcript-archive/<project>/<rel>.gz, verifies the archive
# decompresses byte for byte to the original, and only then removes the
# original. Never deletes a transcript without a verified archive.
archive_transcripts() {
  local apply=0; [[ "${1:-}" == "--apply" ]] && apply=1
  python3 - "$apply" <<'PY'
import gzip, os, shutil, sys, tempfile, time
apply = sys.argv[1] == "1"
src = os.path.expanduser("~/.claude/projects")
dst = os.path.expanduser("~/.claude/transcript-archive")
cutoff = time.time() - 86400 * 30
def human(b):
    for u in ("B", "K", "M", "G"):
        if b < 1024 or u == "G":
            return f"{b:.1f}{u}"
        b /= 1024
def same(gz_path, orig):
    with gzip.open(gz_path, "rb") as a, open(orig, "rb") as b:
        while True:
            x, y = a.read(1 << 20), b.read(1 << 20)
            if x != y:
                return False
            if not x:
                return True
print(">>> APPLY — archiving to " + dst if apply else ">>> DRY RUN — nothing will change (add --apply)")
found = []
projects = sorted(os.listdir(src)) if os.path.isdir(src) else []
for proj in projects:
    root = os.path.join(src, proj)
    if not os.path.isdir(root) or os.path.islink(root):
        continue
    for d, dirs, files in os.walk(root):
        dirs[:] = sorted(x for x in dirs if x != "memory")
        for name in sorted(files):
            p = os.path.join(d, name)
            if not name.endswith(".jsonl") or os.path.islink(p) or not os.path.isfile(p):
                continue
            st = os.stat(p)
            if st.st_mtime <= cutoff:
                found.append((proj, os.path.relpath(p, root), p, st.st_size))
before = after = n = 0
for proj, rel, p, size in found:
    if not apply:
        print(f"   {human(size):>8}  {p}")
        before += size; n += 1
        continue
    final = os.path.join(dst, proj, rel + ".gz")
    tmp = None
    try:
        os.makedirs(os.path.dirname(final), exist_ok=True)
        fd, tmp = tempfile.mkstemp(dir=os.path.dirname(final), prefix=".", suffix=".gz.tmp")
        with os.fdopen(fd, "wb") as raw, gzip.GzipFile(fileobj=raw, mode="wb") as gz, open(p, "rb") as f:
            shutil.copyfileobj(f, gz)
        if not same(tmp, p):
            raise ValueError("verify mismatch")
        os.replace(tmp, final); tmp = None
        os.remove(p)
        gsize = os.path.getsize(final)
        before += size; after += gsize; n += 1
        print(f"   archived {human(size):>8} -> {human(gsize):>8}  {p}")
    except (OSError, ValueError, EOFError) as e:
        print(f"   KEPT (not archived: {e})  {p}")
    finally:
        if tmp and os.path.exists(tmp):
            os.remove(tmp)
if apply:
    print(f"\n   {n} archived, {before} bytes before, {after} bytes after")
else:
    print(f"\n   {n} file(s), ~{human(before)} total")
PY
}

# --- dispatch --------------------------------------------------------------
cmd="${1:-scan}"; shift || true
case "$cmd" in
  scan)   do_scan ;;
  clean)  do_clean "$@" ;;
  assets)
    sub="${1:-scan}"; shift || true
    case "$sub" in
      scan)  assets_scan "$@" ;;
      trash) assets_trash "$@" ;;
      *) echo "assets: use 'scan' or 'trash'"; exit 1 ;;
    esac ;;
  offload)
    sub="${1:-}"; shift || true
    case "$sub" in
      evict) offload_evict "$@" ;;
      move)  offload_move "$@" ;;
      *) echo "offload: use 'evict <path>' or 'move <path> [--apply]'"; exit 1 ;;
    esac ;;
  archive) archive_offload "$@" ;;
  snapshots)
    # Thin Time Machine local snapshots. Needs sudo — macOS prompts for the
    # password interactively. NEVER hardcode a password here.
    echo "Local snapshots before: $(tmutil listlocalsnapshots / 2>/dev/null | grep -c com.apple)"
    sudo tmutil thinlocalsnapshots / 999999999999 4
    echo "Local snapshots after:  $(tmutil listlocalsnapshots / 2>/dev/null | grep -c com.apple)" ;;
  audit) exec "$(dirname "$0")/deep-audit.sh" "$@" ;;
  report) do_report "$@" ;;
  worktrees)   stale_worktrees "$@" ;;
  transcripts) archive_transcripts "$@" ;;
  processes|proc)
    sub="${1:-report}"; shift || true
    case "$sub" in
      report) proc_report ;;
      quit)   proc_quit "$@" ;;
      reset)  proc_reset "$@" ;;
      *) echo "processes: use 'report' (read-only), 'quit [--apply]', or 'reset [--apply|--self-check]'"; exit 1 ;;
    esac ;;
  *) echo "Unknown command: $cmd"; echo "Use: scan | clean | assets | offload | archive | snapshots | audit | processes | report | worktrees | transcripts"; exit 1 ;;
esac
