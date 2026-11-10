#!/usr/bin/env bash
#
# deep-audit.sh — READ-ONLY macOS audit. Changes NOTHING.
# Surfaces: (1) security/malware persistence points, (2) questionable
# system-data bloat with sizes, (3) large local files that are candidates
# for iCloud offload. Every section only reports; you decide what to act on.
#
# Usage: deep-audit.sh [security|malware|extensions|systemdata|space|orphans|unusedapps|largefiles|storage|all]   (default: all)
#   storage = every disk-space check (space map, system data, orphans, unused apps, large files)

set -uo pipefail
HOME_DIR="${HOME}"
SIZE_THRESHOLD_MB="${LARGE_MB:-500}"   # large-file cutoff; override: LARGE_MB=1000 ...

hr(){ printf '\n========== %s ==========\n' "$1"; }
sz(){ du -sh "$1" 2>/dev/null | awk '{print $1}'; }

audit_security() {
  hr "SECURITY / MALWARE PERSISTENCE (read-only)"

  echo "-- System protections --"
  echo -n "  SIP (System Integrity Protection): "; csrutil status 2>/dev/null | sed 's/.*status: //' || echo "unknown"
  echo -n "  Gatekeeper: "; spctl --status 2>/dev/null || echo "unknown"
  local xp="/Library/Apple/System/Library/CoreServices/XProtect.bundle/Contents/Info.plist"
  [[ -f "$xp" ]] && echo "  XProtect version: $(defaults read "$xp" CFBundleShortVersionString 2>/dev/null)"

  echo "-- Launch agents / daemons (persistence — where malware hides) --"
  for d in "${HOME_DIR}/Library/LaunchAgents" "/Library/LaunchAgents" "/Library/LaunchDaemons"; do
    [[ -d "$d" ]] || continue
    echo "  [$d]"
    local found=0 f label
    for f in "$d"/*.plist; do
      [[ -e "$f" ]] || continue
      found=1
      label="$(basename "$f")"
      # Flag ones NOT from obviously-legit vendors
      case "$label" in
        com.apple.*|com.google.*|com.microsoft.*|com.adobe.*|com.docker.*|homebrew.*|com.spotify.*|org.*|com.logi.*|com.amazon.*) printf '     ok   %s\n' "$label" ;;
        *) printf '     >>>  %s   (verify this is expected)\n' "$label" ;;
      esac
    done
    [[ "$found" == "0" ]] && echo "     (none)"
  done

  echo "-- Configuration profiles (adware/MDM often installs these) --"
  profiles list 2>/dev/null | grep -iv "There are no" | head || echo "  (need sudo, or none)"
  profiles status -type enrollment 2>/dev/null | head -2

  echo "-- Third-party kernel/system extensions --"
  kmutil showloaded --list-only 2>/dev/null | awk '$6 !~ /^com\.apple/ {print "     "$6}' | grep -v '^     $' | head || \
    systemextensionsctl list 2>/dev/null | grep -v "com.apple" | head || echo "  (none detected)"

  echo "-- Known adware/PUP footprints --"
  local hits=0 p
  for p in \
    "/Library/Application Support/MacKeeper" "${HOME_DIR}/Library/Application Support/MacKeeper" \
    "/Applications/MacKeeper.app" "/Applications/Advanced Mac Cleaner.app" "/Applications/MacCleanup Pro.app" \
    "/Library/Application Support/Genieo" "/Library/Frameworks/VSearch.framework" \
    "${HOME_DIR}/Library/Application Support/com.genieo"* "/Library/LaunchAgents/com.mackeeper"* \
    "/Applications/MediaAccess.app" "/Applications/Mac Auto Fixer.app" ; do
    [[ -e "$p" ]] && { printf '     >>> FOUND: %s\n' "$p"; hits=1; }
  done
  [[ "$hits" == "0" ]] && echo "     (clean — none of the common adware paths present)"

  echo "-- Browser extensions: see 'audit extensions' (names + risk flags per Chrome profile) --"

  echo "-- For a real malware SCAN (not just persistence review):"
  echo "     • Objective-See KnockKnock/BlockBlock (free): https://objective-see.org/products.html"
  echo "     • Malwarebytes for Mac (free scan)"
}

audit_systemdata() {
  hr "QUESTIONABLE SYSTEM DATA (sizes — you decide)"
  local pairs=(
    "iOS/iPhone backups|${HOME_DIR}/Library/Application Support/MobileSync/Backup"
    "Xcode DerivedData (rebuildable)|${HOME_DIR}/Library/Developer/Xcode/DerivedData"
    "Xcode iOS DeviceSupport (re-downloads)|${HOME_DIR}/Library/Developer/Xcode/iOS DeviceSupport"
    "Xcode Archives|${HOME_DIR}/Library/Developer/Xcode/Archives"
    "iOS Simulators|${HOME_DIR}/Library/Developer/CoreSimulator/Devices"
    "GarageBand/Logic content|${HOME_DIR}/Library/Application Support/GarageBand"
    "Docker data|${HOME_DIR}/Library/Containers/com.docker.docker"
    "Containers (all)|${HOME_DIR}/Library/Containers"
    "Group Containers|${HOME_DIR}/Library/Group Containers"
    "Mail downloads|${HOME_DIR}/Library/Containers/com.apple.mail/Data/Library/Mail Downloads"
    "Old installers in Downloads|${HOME_DIR}/Downloads"
  )
  local item name path
  for item in "${pairs[@]}"; do
    name="${item%%|*}"; path="${item##*|}"
    [[ -e "$path" ]] && printf '  %-40s %6s  %s\n' "$name" "$(sz "$path")" "$path"
  done

  echo "-- Local snapshots (often the biggest hidden 'System Data') --"
  local list tm os; list="$(tmutil listlocalsnapshots / 2>/dev/null)"
  tm="$(grep -c 'com.apple.TimeMachine' <<<"$list")"; os="$(grep -c 'com.apple.os.update' <<<"$list")"
  echo "     $tm Time Machine snapshot(s). Thin with: sudo tmutil thinlocalsnapshots / 999999999999 4"
  echo "     $os macOS-update snapshot(s). macOS manages these; thinning does NOT remove them."

  echo "-- Big .dmg/.pkg installers you can trash after install --"
  find "${HOME_DIR}/Downloads" "${HOME_DIR}/Desktop" -maxdepth 2 -type f \( -iname "*.dmg" -o -iname "*.pkg" \) 2>/dev/null \
    -exec du -h {} \; | sort -rh | head -10 | sed 's/^/     /' || echo "     (none)"
}

audit_largefiles() {
  hr "LARGE LOCAL FILES > ${SIZE_THRESHOLD_MB} MB (iCloud-offload candidates)"
  echo "  ('local' = actually on disk. Files already evicted to iCloud show ~0 and are skipped.)"
  local icloud_root="${HOME_DIR}/Library/Mobile Documents/com~apple~CloudDocs"
  # Scan real user data, skip caches/apps/dev deps/already-cloud
  find "${HOME_DIR}/Desktop" "${HOME_DIR}/Downloads" "${HOME_DIR}/Documents" "${HOME_DIR}/Movies" "${HOME_DIR}/Pictures" "${HOME_DIR}/Developer" \
    -type d \( -name node_modules -o -name ".git" -o -name "*.photoslibrary" -o -name "*.app" \) -prune -o \
    -type f -size +"${SIZE_THRESHOLD_MB}"M -print 2>/dev/null | while IFS= read -r f; do
      # physical blocks: 0 => already evicted to iCloud, no local space used
      local blocks; blocks="$(stat -f%b "$f" 2>/dev/null || echo 1)"
      [[ "$blocks" == "0" ]] && continue
      local loc="local"
      [[ "$f" == "$icloud_root"* || "$f" == "${HOME_DIR}/Desktop"* || "$f" == "${HOME_DIR}/Documents"* ]] && loc="in-iCloudDrive(evictable)"
      printf '  %8s  [%s]  %s\n' "$(du -h "$f" 2>/dev/null | awk '{print $1}')" "$loc" "$f"
    done | sort -rh | head -30
  echo
  echo "  To reclaim local space from a file already in iCloud Drive (Desktop/Docs/iCloud folders):"
  echo "     trevskills-mac-cleanup.sh offload evict \"<path>\"     (keeps it in iCloud, frees local copy)"
  echo "  To move a local file INTO iCloud Drive then free the local copy:"
  echo "     trevskills-mac-cleanup.sh offload move \"<path>\""
}

audit_space() {
  hr "WHERE THE SPACE IS (biggest folders, read-only)"
  local d
  for d in "$HOME_DIR" "$HOME_DIR/Library" "$HOME_DIR/Library/Application Support" "$HOME_DIR/Library/Containers" /Applications /opt/homebrew; do
    [[ -d "$d" ]] || continue
    echo "  [$d]"
    du -xhd1 "$d" 2>/dev/null | sort -rh | sed -n '2,9p' | sed 's/^/     /'
  done
  echo "  Pointers: Library/Messages + com.apple.MobileSMS shrink via Messages → Keep Messages;"
  echo "  ~/.claude/projects is chat history (kept on purpose); vm_bundles = Claude desktop's VM."
}

audit_orphans() {
  hr "LEFTOVER DATA FROM UNINSTALLED APPS (verify, then Trash what you approve)"
  # ponytail: name-matching heuristic (folder name vs installed app names/bundle ids/CLI
  # commands); it can miss renamed vendors or flag a CLI tool's data. It only reports.
  python3 -I - "$HOME_DIR" <<'PY'
import glob, json, os, plistlib, re, shutil, subprocess, sys
home = sys.argv[1]
norm = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
known = set()
for app in glob.glob("/Applications/*.app") + glob.glob("/Applications/*/*.app") + glob.glob(home + "/Applications/*.app") + glob.glob("/System/Applications/*.app"):
    known.add(norm(os.path.basename(app)[:-4]))
    try:
        with open(app + "/Contents/Info.plist", "rb") as f: p = plistlib.load(f)
        for k in ("CFBundleIdentifier", "CFBundleName"):
            if p.get(k): known.add(norm(p[k]))
    except Exception: pass
known.discard("")
def installed(name):
    n = norm(name)
    if len(n) < 3: return True
    if shutil.which(name.lstrip(".")): return True
    vendor = re.match(r"(?:com|org|io|net)\.([^.]+)\.", name)  # com.adobe.dunamis → any Adobe app
    if vendor and any(norm(vendor.group(1)) in k for k in known): return True
    return any(n in k or (len(k) > 3 and k in n) for k in known)
GENERIC = {"Caches", "CrashReporter", ".cache", ".config", ".local", ".npm", ".Trash", ".ssh", ".gnupg", ".claude", ".zsh_sessions", ".oh-my-zsh", ".nvm", ".cargo", ".rustup", ".pyenv", ".docker", ".vscode"}
cands = [os.path.join(home, "Library/Application Support", d) for d in os.listdir(os.path.join(home, "Library/Application Support"))
         if not d.startswith(("com.apple", "Apple", ".")) and d not in GENERIC]
cands += [os.path.join(home, d) for d in os.listdir(home) if d.startswith(".") and d not in GENERIC and os.path.isdir(os.path.join(home, d))]
rows = []
for c in cands:
    if installed(os.path.basename(c)): continue
    kb = int(subprocess.run(["du", "-sk", c], capture_output=True, text=True).stdout.split()[0] or 0)
    if kb >= 100 * 1024: rows.append((kb, c))
for kb, c in sorted(rows, reverse=True):
    print(f"  {kb/1048576:6.1f}G  {c}")
if not rows: print("  (none over 100 MB)")
print("-- Chrome native-messaging hosts pointing at a missing app --")
hit = 0
for f in glob.glob(home + "/Library/Application Support/Google/Chrome/NativeMessagingHosts/*.json"):
    try: path = json.load(open(f)).get("path", "")
    except Exception: continue
    if path and not os.path.exists(path): print(f"  >>> {f}  ->  {path}"); hit = 1
if not hit: print("  (none)")
PY
}

audit_unusedapps() {
  hr "APPS NOT OPENED IN ${UNUSED_DAYS:-180}+ DAYS (reinstallable; you decide)"
  local app last days now; now="$(date +%s)"
  for app in /Applications/*.app; do
    [[ "$(defaults read "$app/Contents/Info" CFBundleIdentifier 2>/dev/null)" == com.apple.* ]] && continue
    last="$(mdls -name kMDItemLastUsedDate -raw "$app" 2>/dev/null)"
    if [[ "$last" == "(null)" || -z "$last" ]]; then days="?"
    else days=$(( (now - $(date -j -f '%Y-%m-%d %H:%M:%S %z' "$last" +%s 2>/dev/null || echo "$now")) / 86400 ))
         [[ "$days" -lt "${UNUSED_DAYS:-180}" ]] && continue
    fi
    printf '  %6s  last used: %-6s  %s\n' "$(sz "$app")" "$days" "$app"
  done | sort -rh
  echo "  '?' = macOS has no open date (never opened, or only launched in the background, e.g. Karabiner). Check before removing."
  echo "  Each app's data in ~/Library/Application Support goes with it; see 'audit orphans' after."
}

audit_extensions() {
  hr "CHROME EXTENSIONS BY PROFILE (read-only)"
  local root="${HOME_DIR}/Library/Application Support/Google/Chrome"
  [[ -d "$root" ]] || { echo "  (Chrome not installed)"; return; }
  # -I: don't import modules from the cwd or the extension folders being read
  python3 -I - "$root" <<'PY'
import json, os, re, sys
root = sys.argv[1]
def load(p):
    try:
        with open(p, encoding="utf-8-sig") as f: return json.load(f)
    except Exception: return {}
names = {k: v.get("name", k) for k, v in load(os.path.join(root, "Local State")).get("profile", {}).get("info_cache", {}).items()}
def msg(text, d, m):
    hit = re.fullmatch(r"__MSG_(\w+)__", text or "")
    if not hit: return text or ""
    for loc in (m.get("default_locale"), "en", "en_US"):
        if not loc: continue
        msgs = {k.lower(): v for k, v in load(os.path.join(d, "_locales", loc, "messages.json")).items()}
        v = msgs.get(hit.group(1).lower(), {}).get("message")
        if v: return v
    return text
RISKS = [
    (r"\bvpn\b|proxy", "VPN/proxy: can see all browsing traffic"),
    (r"coupon|cash ?back|honey|coupert|rakuten|capital one shopping", "coupon/cashback: reads every shopping page"),
    (r"wallet|metamask|phantom|crypto", "crypto wallet: confirm the seed phrase is backed up and no funds remain before removing"),
    (r"\b(ai|gpt|chatgpt|seo|summari[sz]e|assistant)\b", "AI/SEO page reader: sends page content to its server"),
]
BROAD = {"<all_urls>", "*://*/*", "http://*/*", "https://*/*"}
for prof in sorted(os.listdir(root)):
    ext = os.path.join(root, prof, "Extensions")
    if not os.path.isdir(ext): continue
    print(f"  [{names.get(prof, prof)}]  ({prof})")
    rows = []
    for eid in sorted(os.listdir(ext)):
        vers = sorted(v for v in os.listdir(os.path.join(ext, eid)) if os.path.isfile(os.path.join(ext, eid, v, "manifest.json"))) if os.path.isdir(os.path.join(ext, eid)) else []
        if not vers: continue
        d = os.path.join(ext, eid, vers[-1]); m = load(os.path.join(d, "manifest.json"))
        name = msg(m.get("name"), d, m); desc = msg(m.get("description"), d, m)
        perms = set(map(str, m.get("permissions", []) + m.get("host_permissions", [])))
        for cs in m.get("content_scripts", []): perms |= set(cs.get("matches", []))
        flags = [why for rx, why in RISKS if re.search(rx, f"{name} {desc}", re.I)]
        if perms & BROAD: flags.append("broad host access (every site)")
        rows.append((not flags, name, eid, flags))
    if not rows: print("     (none)")
    for _, name, eid, flags in sorted(rows):
        print(f"     {'>>>' if flags else 'ok '}  {name}  [{eid}]")
        for f in flags: print(f"            - {f}")
PY
  echo "  Remove an extension yourself in chrome://extensions (open the profile first);"
  echo "  browser automation can't open that page. Broad access alone is common (password"
  echo "  managers, ad blockers); it matters when you don't recognise the extension."
}

audit_malware() {
  hr "DEEP MALWARE SWEEP (read-only, goes beyond signature-presence)"
  echo "Verifies persistence CRYPTOGRAPHICALLY and checks the vectors malware"
  echo "actually uses. Known-benign noise is annotated so real signal stands out."

  echo "-- 1. Crypto-verify every LaunchAgent/Daemon target binary --"
  local d f prog out any=0
  for d in /Library/LaunchAgents /Library/LaunchDaemons "${HOME_DIR}/Library/LaunchAgents"; do
    for f in "$d"/*.plist; do
      [[ -e "$f" ]] || continue
      prog="$(/usr/libexec/PlistBuddy -c 'Print :Program' "$f" 2>/dev/null)"
      [[ -z "$prog" ]] && prog="$(/usr/libexec/PlistBuddy -c 'Print :ProgramArguments:0' "$f" 2>/dev/null)"
      [[ -z "$prog" || "$prog" == *"Doesn't Exist"* ]] && continue
      if [[ ! -e "$prog" ]]; then
        printf '   >>> ORPHAN: %s -> missing binary %s\n' "$(basename "$f")" "$prog"; any=1
      else
        out="$(codesign --verify --strict "$prog" 2>&1)"
        case "$out" in
          "") ;;                                   # valid
          *"Permission denied"*) ;;                # needs sudo to read; not a signal
          *"not signed at all"*)
            printf '   ~   UNSIGNED (verify manually): %s -> %s\n' "$(basename "$f")" "$prog"; any=1 ;;
          *) printf '   >>> VERIFY-FAIL: %s -> %s :: %s\n' "$(basename "$f")" "$prog" "$(echo "$out" | head -1)"; any=1 ;;
        esac
      fi
    done
  done
  [[ "$any" == "0" ]] && echo "   (all persistence binaries present + validly signed)"
  echo "   NOTE: Homebrew binaries + many open-source DBs (Firebird/Postgres) are"
  echo "   legitimately unsigned; orphans usually mean uninstalled apps left a plist."

  echo "-- 2. /etc/hosts redirects (phishing/blocklist tampering) --"
  grep -vE '^\s*#|^\s*$|127\.0\.0\.1|::1|255\.255|fe80|ff00|ff02' /etc/hosts 2>/dev/null | sed 's/^/     /' || true
  echo "     (nothing above = clean)"

  echo "-- 3. Cron + login items --"
  crontab -l 2>/dev/null | grep -vE '^\s*#|^\s*$' | sed 's/^/     cron: /' || echo "     (no user crontab)"
  osascript -e 'tell application "System Events" to get the name of every login item' 2>/dev/null | sed 's/^/     login-item: /' || true

  echo "-- 4. DYLD injection in launch plists (library hijack) --"
  grep -rli "DYLD_INSERT_LIBRARIES" /Library/LaunchAgents /Library/LaunchDaemons "${HOME_DIR}/Library/LaunchAgents" 2>/dev/null \
    | sed 's/^/     >>> DYLD inject: /' || true
  echo "     (nothing above = no DYLD injection configured)"

  echo "-- 5. Network listeners (accepting connections; loopback hidden) --"
  lsof -nP -iTCP -sTCP:LISTEN 2>/dev/null | awk 'NR>1 && $9 !~ /127.0.0.1|\[::1\]/{print "     "$1"  "$9}' | sort -u | head -20
  echo "     (Apple AirPlay uses *:5000/*:7000 via ControlCenter; dev servers e.g. *:3000 = yours)"

  echo "-- 6. Recently-dropped executables (last 21 days, common malware paths) --"
  local dd hit=0
  for dd in /usr/local/bin "${HOME_DIR}/bin" /tmp /var/tmp "${HOME_DIR}/Library/Application Support" "${HOME_DIR}/Library/LaunchAgents" /Library/LaunchAgents; do
    [[ -d "$dd" ]] || continue
    find "$dd" -maxdepth 2 -type f -perm +111 -mtime -21 2>/dev/null \
      | grep -vE 'node_modules|/Code/|/Cursor/|homebrew|/npm|\.dylib$' | head -15 | while IFS= read -r x; do echo "     $x"; done
  done
  echo "     (nothing above = no new executables dropped)"

  echo "-- For DEFINITIVE certainty (behavioral + known-signature database): --"
  echo "     • Objective-See KnockKnock (persistence scan) + BlockBlock (live monitor): objective-see.org"
  echo "     • Malwarebytes for Mac — free on-demand scan"
  echo "   A shell audit finds persistence + tampering; a maintained scanner adds a threat DB."
}

case "${1:-all}" in
  security)   audit_security ;;
  systemdata) audit_systemdata ;;
  largefiles) audit_largefiles ;;
  malware)    audit_malware ;;
  extensions) audit_extensions ;;
  space)      audit_space ;;
  orphans)    audit_orphans ;;
  unusedapps) audit_unusedapps ;;
  storage)    audit_space; audit_systemdata; audit_orphans; audit_unusedapps; audit_largefiles ;;
  all)        audit_security; audit_malware; audit_extensions; audit_systemdata; audit_orphans; audit_unusedapps; audit_largefiles ;;
  *) echo "Usage: deep-audit.sh [security|malware|extensions|systemdata|space|orphans|unusedapps|largefiles|storage|all]"; exit 1 ;;
esac
echo; echo "(Audit complete — nothing was changed.)"
