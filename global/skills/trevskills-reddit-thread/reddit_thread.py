#!/usr/bin/env python3
"""Read a Reddit thread from a URL via the official OAuth API (stdlib only)."""
import base64, json, os, re, sys, urllib.parse, urllib.request

ENV_PATH = os.path.expanduser("~/.config/trevskills-reddit/.env")
UA = "trevskills-reddit-thread/1.0"


class RedditError(Exception):
    pass


def extract_post_id(url):
    u = urllib.parse.urlparse(url.strip())
    host = (u.hostname or "").lower()
    parts = [p for p in u.path.split("/") if p]
    if host == "redd.it" and parts and re.fullmatch(r"[a-z0-9]+", parts[0]):
        return parts[0]
    if host == "reddit.com" or host.endswith(".reddit.com"):
        if "comments" in parts:
            i = parts.index("comments")
            if i + 1 < len(parts) and re.fullmatch(r"[a-z0-9]+", parts[i + 1]):
                return parts[i + 1]
    raise ValueError("not a reddit thread URL: %s" % url)


def load_env(path):
    out = {}
    try:
        with open(path) as f:
            lines = f.read().splitlines()
    except OSError:
        return out
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        v = v.strip()
        if len(v) >= 2 and v[0] == v[-1] and v[0] in "'\"":
            v = v[1:-1]
        if v:
            out[k.strip()] = v
    return out


def format_thread(data):
    post = data[0]["data"]["children"][0]["data"]
    lines = [
        "r/%s: %s" % (post.get("subreddit"), post.get("title")),
        "by %s (%s points)" % (post.get("author"), post.get("score")),
        "https://www.reddit.com%s" % post.get("permalink", ""),
        "",
    ]
    if post.get("selftext"):
        lines += [post["selftext"], ""]

    def walk(children, depth):
        for c in children:
            d = c.get("data", {})
            pad = "  " * depth
            if c.get("kind") == "more":
                lines.append("%s[%s more replies]" % (pad, d.get("count", 0)))
                continue
            body = (d.get("body") or "").replace("\n", "\n" + pad + "  ")
            lines.append("%s%s (%s): %s" % (pad, d.get("author"), d.get("score"), body))
            replies = d.get("replies")
            if isinstance(replies, dict):
                walk(replies["data"]["children"], depth + 1)

    walk(data[1]["data"]["children"], 0)
    return "\n".join(lines)


def http(req):
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def main(argv):
    try:
        if len(argv) != 1:
            raise RedditError("usage: reddit_thread.py <reddit thread url>")
        try:
            pid = extract_post_id(argv[0])
        except ValueError as e:
            raise RedditError(str(e))
        env = {**load_env(ENV_PATH)}
        cid = os.environ.get("REDDIT_CLIENT_ID") or env.get("REDDIT_CLIENT_ID")
        sec = os.environ.get("REDDIT_CLIENT_SECRET") or env.get("REDDIT_CLIENT_SECRET")
        if not cid or not sec:
            raise RedditError("missing REDDIT_CLIENT_ID / REDDIT_CLIENT_SECRET (set them in %s)" % ENV_PATH)
        auth = base64.b64encode(("%s:%s" % (cid, sec)).encode()).decode()
        try:
            tok = http(urllib.request.Request(
                "https://www.reddit.com/api/v1/access_token",
                data=b"grant_type=client_credentials",
                headers={"Authorization": "Basic " + auth, "User-Agent": UA}))["access_token"]
            data = http(urllib.request.Request(
                "https://oauth.reddit.com/comments/%s?raw_json=1" % pid,
                headers={"Authorization": "bearer " + tok, "User-Agent": UA}))
        except Exception as e:  # never echo e: it may carry request details
            code = getattr(e, "code", None)
            raise RedditError("request failed (%s)" % (("HTTP %s" % code) if code else type(e).__name__))
        print(format_thread(data))
        return 0
    except RedditError as e:
        print("reddit_thread: %s" % e, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
