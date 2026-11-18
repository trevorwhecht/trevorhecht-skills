---
name: trevskills-reddit-thread
description: Use when given a reddit.com or redd.it thread URL to read — "read this reddit thread", "what do the comments say", or /trevskills-reddit-thread <url>. Fetches the post and comment tree through Reddit's official OAuth API and prints it as plain text. Official API only, no mirrors or scraping.
allowed-tools: Bash(python3 *)
---

# Reddit thread reader

Prints one Reddit thread (post plus indented comments) from its URL.

## Why this exists

On 2026-11-17 Reddit refused curl, old.reddit, the `.json` endpoint, WebFetch and the Chrome extension, and the thread had to be pasted by hand. The last30days skill does not cover this: it has no single-thread command (only topic search), its thread fetch uses the same unauthenticated `.json` endpoint that was refused, and its other path scrapes HTML.

## Setup (once)

1. Go to reddit.com/prefs/apps and create an app of type "script".
2. Create `~/.config/trevskills-reddit/.env` (outside any repo) and `chmod 600` it:

```
REDDIT_CLIENT_ID=<id under the app name>
REDDIT_CLIENT_SECRET=<secret>
```

The same-named environment variables also work. Never print or commit these.

## Usage

```
python3 ~/.claude/skills/trevskills-reddit-thread/reddit_thread.py <thread url>
```

Accepts reddit.com, old.reddit.com and redd.it links. Failures print one `reddit_thread: ...` line and exit 1.

## Rules

- Official API only (client-credentials OAuth, `oauth.reddit.com`). No mirrors, scraping, cookies or alternate front ends; if the API fails, tell the user and ask them to paste the thread.
- "More comments" stubs show as `[N more replies]` and are not expanded.
- Read only: no search, listings, posting or voting.
