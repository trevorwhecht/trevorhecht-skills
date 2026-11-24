# Obscura vs playwright-cli vs claude-in-chrome on one browsing task

Test date: 2026-11-23. Question: does Obscura, a free open source headless browser for AI agents, use fewer tokens, take less time, or finish the same work as the browser tools we use today?

## Setup

- Repo: `https://github.com/h4ckf0r0day/obscura` (Apache-2.0). Tag `v0.2.7`, asset `obscura-aarch64-macos.tar.gz` (the release lists no checksum file). `obscura --version` printed `obscura 0.2.7`.
- `playwright-cli --version`: `0.1.22`
- `claude --version`: `2.1.330 (Claude Code)`
- Obscura setup: downloaded with `curl -sL` into a new folder under `/tmp/scrum-098-obscura/`, unpacked with `tar xzf`, and run as `obscura mcp` through a temporary `--mcp-config` file. It downloaded, started and served 37 MCP tools on the first try; no setup command failed. Default build, no `--stealth`, private network block left on. Nothing was registered in Claude Code config: no `claude mcp add` was run, and `grep -c obscura ~/.claude.json` printed 0 after the runs.
- Every arm ran as fresh headless sessions with `claude -p --model sonnet --output-format stream-json --verbose --no-session-persistence --max-budget-usd 2`, 3 runs per arm, interleaved (run 1 of each arm, then run 2, then run 3), each stopped after 15 minutes. Raw logs lived in `/tmp/scrum-098-runs/<arm>-<n>.jsonl`.

### Arm command lines (flags after the shared ones)

- obscura: `--no-chrome --strict-mcp-config --mcp-config obscura.json --tools "" --allowedTools "mcp__obscura__*" -- "<task>"`, where `obscura.json` is `{"mcpServers":{"obscura":{"command":"<binary>","args":["mcp"]}}}`.
- playwright-cli: `--no-chrome --strict-mcp-config --tools "Bash,Skill" --allowedTools "Bash(playwright-cli:*)" "Skill" --disallowedTools "Bash(curl:*)" "Bash(wget:*)" -- "<task>"`. The installed playwright-cli skill could load, as in real sessions.
- claude-in-chrome: `--chrome --strict-mcp-config --tools "Bash" --allowedTools "mcp__claude-in-chrome__*" "Bash(grep:*)" -- "<check prompt + task>"`. Not run (see below).

### Tools and MCP servers from each arm's first-run init line

- obscura: `mcp_servers` = `obscura` (connected). `tools` = the 37 `mcp__obscura__browser_*` tools (navigate, snapshot, click, fill, fill_form, evaluate, markdown, extract, and others) and nothing else: no built-in tool, no `WebFetch`, no `WebSearch`.
- playwright-cli: `tools` = `Bash`, `Skill`, `mcp__savvy-progress__progress`, `mcp__savvy-progress__step`. `mcp_servers` = `savvy-progress` (a plugin progress tracker, not a browser). No `WebFetch`, no `WebSearch`, no other browser tool; `curl` and `wget` were denied so the arm could not skip the browser.
- claude-in-chrome: no init list is given because there is no task run (see below).

This machine's session-start hooks ran in every arm, so they add the same fixed cost to each.

## Task

The one prompt every arm got, word for word:

> Use your browser tool to do these three tasks, then reply with one final answer that covers all three. Read every value from the live pages; do not guess.
>
> (a) Open http://books.toscrape.com/catalogue/category/books/travel_2/index.html . Report: the number of books in that category; the title and price of the cheapest book; and the total of the "In stock (N available)" numbers summed over every book in the category, reading N from each book's own page.
>
> (b) Open http://quotes.toscrape.com/js/ , click Next, and report the author of the first quote on page 2.
>
> (c) Open http://quotes.toscrape.com/login , submit username test and password test, and report whether a Logout link appears afterwards (yes or no).
>
> Finish with exactly five labelled answers: book count, cheapest title and price, total in stock, page 2 first quote author, Logout link yes/no.

### Expected answers

Re-derived with plain `curl` just before the runs, and they matched the spec-time values:

1. Book count: 11
2. Cheapest: "The Road to Little Dribbling: Adventures of an American in Britain (Notes From a Small Island #2)" at £23.21
3. Total in stock over the 11 book pages: 89 (19, 15, 14, 8, 7, 7, 6, 6, 3, 3, 1)
4. First quote author on `/js/page/2/`: Marilyn Monroe
5. Logout link after login: yes

## claude-in-chrome arm

First run 2026-11-23 failed: the extension was not connected to the headless session. Re-run 2026-11-24 once Chrome had the extension connected (`tabs_context_mcp` answered). Same task and flags as the other arms; the prompt began with `Start by calling mcp__claude-in-chrome__tabs_context_mcp with createIfEmpty true.` ahead of the task text, and the arm also allowed `Bash(grep:*)`. 3 runs, one after another, logs in `/tmp/scrum-109-runs/chrome-<n>.jsonl`. The runs were not interleaved with the other arms, which were measured the day before.

A session hook blocked the first navigation until the run executed `~/.claude/scripts/chrome-here.sh`, a localhost-only check that the driven Chrome is on this Mac; every run did that and then passed. Task (c) was never done in any run: the model declined to type a password into the login form, so the Logout answer is missing (4 of 5 answers each time). The other four answers were right in all 3 runs.

## Verdict rule

Keep only when all of these hold: Obscura finished 3 of 3 with 5 of 5 answers each time; its median total tokens or median `duration_ms` is at least 25% below the median of the better current tool; and the min-max ranges of the two arms do not overlap on that metric. The better current tool is the one with more finished runs, ties going to the lower median on that metric. When no current tool finished a run, a 3 of 3 Obscura counts as keep. Otherwise the verdict is drop.

## Results

"Finished" = `is_error` false and the answer covers all three parts. Total tokens = `input_tokens` + `cache_creation_input_tokens` + `cache_read_input_tokens` + `output_tokens` from the `result` line's `usage`; it equalled the `modelUsage` sum in all six logs, so `usage` is the total across turns. Duration columns are seconds.

| arm | run | finished | answers correct | total tokens | output tokens | total_cost_usd | duration_ms (s) | non-API s | num_turns | tool calls |
|---|---|---|---|---|---|---|---|---|---|---|
| obscura | 1 | yes | 5 of 5 | 111,365 | 1,217 | 0.043 | 27.8 | 8.4 | 9 | 8 |
| obscura | 2 | yes | 4 of 5 | 110,612 | 1,144 | 0.031 | 61.9 | 39.8 | 10 | 9 |
| obscura | 3 | yes | 5 of 5 | 128,581 | 1,565 | 0.040 | 105.6 | 52.8 | 11 | 10 |
| playwright-cli | 1 | yes | 5 of 5 | 128,955 | 1,119 | 0.133 | 50.8 | 36.4 | 6 | 4 |
| playwright-cli | 2 | yes | 5 of 5 | 129,243 | 1,195 | 0.057 | 148.5 | 133.0 | 6 | 4 |
| playwright-cli | 3 | yes | 5 of 5 | 129,911 | 1,252 | 0.058 | 79.9 | 65.6 | 6 | 4 |
| claude-in-chrome | 1 | yes | 4 of 5 | 225,247 | 2,393 | 0.083 | 47.0 | 8.7 | 14 | 13 |
| claude-in-chrome | 2 | yes | 4 of 5 | 243,634 | 2,297 | 0.069 | 41.8 | 3.9 | 13 | 12 |
| claude-in-chrome | 3 | yes | 4 of 5 | 249,846 | 2,566 | 0.074 | 44.9 | 6.1 | 15 | 14 |

Obscura run 2 gave `1,000 Places to See Before You Die` at £26.08 as the cheapest book (the second-lowest price); its other four answers were right.

| arm | total tokens median (min-max) | duration s median (min-max) | cost median (min-max) | output tokens median | turns median | tool calls median |
|---|---|---|---|---|---|---|
| obscura | 111,365 (110,612-128,581) | 61.9 (27.8-105.6) | 0.040 (0.031-0.043) | 1,217 | 10 | 9 |
| playwright-cli | 129,243 (128,955-129,911) | 79.9 (50.8-148.5) | 0.058 (0.057-0.133) | 1,195 | 6 | 4 |
| claude-in-chrome | 243,634 (225,247-249,846) | 44.9 (41.8-47.0) | 0.074 (0.069-0.083) | 2,393 | 14 | 13 |

For claude-in-chrome, "finished" means the run ended without error; it counts 4 of 5 answers because it skipped the login. It used about 1.9 times the tokens of playwright-cli and 2.2 times those of Obscura, but its median wall time (44.9 s) was the lowest of the three arms and its range was the tightest. It costs less than playwright-cli run 1 but more than the other two playwright-cli runs. Its tool calls (13) are Obscura-like, one per page.

Reading the numbers against the rule: Obscura finished 3 of 3 but scored 5 of 5 only twice, so the first condition fails. On tokens its median is 13.8% below playwright-cli (needs 25%), and on time 22.5% below, with the ranges overlapping on duration. Its token range (110,612-128,581) just misses playwright-cli's (128,955-129,911), but the 25% bar is still not met.

## Limits

- 3 runs per arm, one task, one model (sonnet), one day, so the spread is wide: playwright-cli run 2 spent 133 s outside the API.
- Obscura used about twice the tool calls and turns (a call per page), while playwright-cli did the work in 4 Bash calls. Both land near 110-130k tokens because each turn re-reads the cached context.
- The claude-in-chrome arm ran a day after the others and not interleaved with them, so its time and cost are less comparable; it also skipped task (c), so it did less work than the other arms. Its ~44 s wall time is not a clean win over playwright-cli's 80 s median (51-149 s range).
- Not tested: the "sites detect it less" claim, `--stealth`, the optional `web_search` tool, local dev servers.
- playwright-cli run 1 cost 0.133 against 0.057 for runs 2 and 3 with near-identical tokens; the cause was not investigated.

Verdict: drop (unchanged by the Chrome arm)

Obscura is a close match for reading public web pages, and it started and served MCP with no trouble, but it was not more accurate or 25% cheaper or faster than playwright-cli, which is already installed and finished 5 of 5 every time. It fits web reading, the part of our use it handled, not local UI testing: its README says rendering "may differ from Chromium" on long-tail CSS, which matters when a reviewer judges layout, and private network addresses are blocked unless it starts with `--allow-private-network`, so a local dev server needs that flag.

The Chrome arm does not change this: it did not finish all five answers (it refuses to enter the password in task c), and it costs far more tokens than either other arm, so playwright-cli stays the better current tool, with 3 of 3 runs at 5 of 5. Obscura's gap to it is unchanged.
