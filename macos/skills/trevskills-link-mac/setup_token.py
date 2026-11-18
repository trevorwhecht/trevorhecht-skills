# Run `claude setup-token` on a worker Mac over SSH in a pty; URL -> url.txt, code read from code.txt,
# token written straight to the worker's token file (never printed).
# Usage: setup_token.py <ssh-alias> owa|main   (work files in /tmp/link-mac-<alias>-<account>/)
import os, pty, re, select, struct, fcntl, termios, subprocess, sys, time
from pathlib import Path

alias, acct = sys.argv[1], sys.argv[2]
if alias.startswith("-") or acct not in ("owa", "main"):
    sys.exit("usage: setup_token.py <ssh-alias> owa|main")
D = Path(f"/tmp/link-mac-{alias}-{acct}")
D.mkdir(exist_ok=True)
cfg, dest = (("CLAUDE_CONFIG_DIR=~/.claude-owa ", "~/.claude-owa/oauth-token") if acct == "owa"
             else ("", "~/.claude/oauth-token"))
for f in ("url.txt", "code.txt"):
    (D / f).unlink(missing_ok=True)
pid, fd = pty.fork()
if pid == 0:
    os.execvp("ssh", ["ssh", "-tt", alias, f"stty cols 2000; {cfg}~/.local/bin/claude setup-token"])
fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", 50, 2000, 0, 0))
buf, sent, deadline = "", False, time.time() + 3600
ansi = lambda s: re.sub(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b\][^\x07]*\x07", "", s)
strip = lambda s: re.sub(r"[\r\n]", "", ansi(s))
while time.time() < deadline:
    r, _, _ = select.select([fd], [], [], 1)
    if r:
        try:
            chunk = os.read(fd, 65536).decode(errors="ignore")
        except OSError:
            break
        if not chunk:
            break
        buf += chunk
    flat = strip(buf)
    if not r and not (D / "url.txt").exists():  # only once output has paused, so the URL is complete
        m = re.search(r"https://claude\.(ai|com)/\S*?oauth/authorize\?\S*?state=[A-Za-z0-9_\-]{43}", flat)
        if m:
            (D / "url.txt").write_text(m.group(0))
            print("URL ready", flush=True)
    if not sent and (D / "code.txt").exists():
        os.write(fd, (D / "code.txt").read_text().strip().encode())
        time.sleep(1.5)
        os.write(fd, b"\r")  # separate write: Ink treats one chunk with \r as a paste, not Enter
        sent = True
        print("code sent", flush=True)
    (D / "screen.txt").write_text(re.sub(r"sk-ant-\S+", "[TOKEN]", flat[-1500:]))
    # match before newlines are removed, or the next line ("Store this token securely") glues on
    t = re.search(r"sk-ant-oat01-[A-Za-z0-9_\-]{20,}", ansi(buf))
    if t:
        p = subprocess.run(["ssh", alias, f"umask 077; cat > {dest}; chmod 600 {dest}"], input=t.group(0).encode())
        print("token saved" if p.returncode == 0 else "token save FAILED", flush=True)
        break
else:
    print("timed out", flush=True)
if not (D / "url.txt").exists():
    print("no URL seen; tail:", strip(buf)[-400:], flush=True)
