---
name: trevskills-owa-message-check
description: One follow-up check for One With Arts (OWA) work across texts (iMessage/SMS), the onewitharts Gmail and OWA Instagram DMs. Finds who still needs a reply, merges each person across channels, checks the call log, and prints organized tables plus a draft reply for each row. Never sends. Use for /trevskills-owa-message-check, "check my messages", "who needs a reply", "OWA inbox", "follow-up check".
---

# OWA message check

Read-only. This skill reads messages and writes drafts; it never sends, marks read, or edits anything.
Run all three sources every run, even when one looks quiet.

## 1. Gather (all three sources, every run)

Window: the last **30 days**. For threads with a 🌀 contact (customer) that end on **their** message, look back further
(an old customer ask that ended on their side is still open, however old).

**Texts (iMessage/SMS).** `~/Library/Messages/chat.db`, opened read-only (`sqlite3 'file:...?mode=ro' -uri`, or
`sqlite3.connect("file:...?mode=ro", uri=True)`). Scan **every** one-to-one thread from the window, whichever
side spoke last (Trevor-spoke-last threads feed *Stale, not resolved*), not only 🌀 contacts: unsaved numbers and
untagged people ask for work too.
- Many sent texts have `text` NULL and live only in `attributedBody`; a raw query shows them as "[attachment]". Decode
  every such row with messageManager's `decode_attributed_body`
  (`~/Developer/repos/python/messageManager/message_manager/core/imessage.py`) before deciding who spoke last.
  Never call a thread unanswered from the raw `text` column alone.
- Re-check each thread you are about to list right before listing it: if Trevor replied since, it is not waiting.

**Email.** The onewitharts Gmail through the Gmail MCP: `search_threads` (e.g. `newer_than:30d -category:promotions`),
then `get_thread` on each candidate to see who wrote last.

**Instagram DMs.** OWA's Instagram through the Graph API at `graph.facebook.com` (graph.instagram.com rejects this
token) with the Page token `INSTAGRAM_ACCESS_TOKEN` (and the other `INSTAGRAM_*` ids) from the onewitharts repo's
`.env.local`. Load it into the environment in the same shell command that calls `curl`; never print, echo or log the
token. List conversations, then messages per conversation, to see who wrote last and when.

**Call log.** `~/Library/Application Support/CallHistoryDB/CallHistory.storedata`, table `ZCALLRECORD`, opened read-only.
Keep each call's number and date (Core Data dates are seconds since 2001-01-01) for step 4.

## 2. Skip

Drop these before any judgement:
- Contacts tagged 📦 (supplier/vendor/outsourcing) or 💧 (fellow printer).
- Family and friends chatter, social-only contacts. A 🌀 tag can be wrong: before listing someone as a customer, check
  the thread reads like work. A friend with a stray 🌀 is skipped and named in the reply so Trevor can fix the tag.
  Never draft work texts to friends.
- Tapbacks/reactions, short codes and 2FA codes, group chats.
- Newsletters, receipts, notifications, marketing mail.

## 3. One row per person

Merge each person across channels into **one row**: one person, one thread of work. If you are already texting
someone, their email or DM about the same work is not a separate item; list every channel in the Source column.

Know who they are first. Look each number/handle/email up in Contacts (all sources) and use names, never bare
numbers: the Contacts name, else the business or order name from the thread, else `new number (…1234)` with the last
four digits. A number saved in Contacts means they already know Trevor, so a draft never opens with an introduction.

## 4. Decide (Jev, not Claude)

Every yes/no about the text itself follows the Jev rule in global CLAUDE.md: ask Jev, and use Claude only to write the
drafts. Pipe one line per person (name, source, last few messages, who spoke last) through
`~/.claude/scripts/jev-rank.py "<question>" --min 0.5` and treat a listed line as yes. Flatten each message's newlines
to single spaces first, so each person is exactly one line. Questions:
- "Is this a work ask about printing, an order, a quote, pricing, artwork, pickup or payment?"
- "Does the last message need a reply from Trevor?"
- "Is this work resolved (order placed, paid or picked up, or a clear thanks, all set)?"

Jev reads text only; decide an image from its thread context, never as if seen. If Jev fails, say so in the report
and decide by reading the short list yourself, marking those rows "(no Jev)".

Then place each person:
- **They spoke last, a call after their last message** (call log, same number) → *Maybe sorted by a call*. Its draft
  answers their open item from their last message, written as if the call never happened; it never mentions the call
  and never asks "all good?".
- **They spoke last, a work ask** → *Order asks waiting*. Order asks get a reply the same day, so they go first.
- **They spoke last, needs a reply, not a work ask** → *Other replies waiting*.
- **Trevor spoke last, not resolved, quiet 3+ days, within 30 days** → *Stale, not resolved*.
- Anything else is left out.

## 5. Output

Organized markdown tables, in this order. Every table has a **Source** column (`Text`, `Email`, `Insta`, or several
joined with ` + `) and a last **Draft** column (rules in section 6). An empty table is the heading plus one line: `None.`

### Order asks waiting
Oldest first.

| Name | Source | Waiting | Gist | Draft |
|---|---|---|---|---|

### Other replies waiting
Oldest first.

| Name | Source | Waiting | Gist | Draft |
|---|---|---|---|---|

### Stale, not resolved

| Name | Source | Quiet for | Last message (who) | What's open | Draft |
|---|---|---|---|---|---|

### Maybe sorted by a call

| Name | Source | Call date | Their last message | Draft |
|---|---|---|---|---|

`Waiting` and `Quiet for` are durations since the last message (`3 h`, `2 d`, `3 wk`). `Gist` and `What's open` are
one short line each.

## 6. Drafts (the Draft column)

Every row in all four tables gets a draft in its **Draft** cell, written with the `trevskills-email` skill (Trevor's
voice, the OWA profile) for the channel they last used. One line per cell: a multi-line email draft is written on one
line with its greeting and sign-off kept. Stale rows get a short nudge; *Maybe sorted by a call* rows get a draft that
answers their open item from their last message, as if the call never happened (no mention of the call, no "all good?").

A step Trevor must do first goes in front in italics (e.g. *Update quote 311 first.*). An Instagram row whose last DM
from them is over 24 h old starts with *Send in the Instagram app (past 24 h).* (the API rejects replies after 24 h).

The skill never sends anything. Trevor sends each draft himself.

## Example

```
### Order asks waiting
| Name | Source | Waiting | Gist | Draft |
|---|---|---|---|---|
| Sam (Corner Café 🌀) | Text + Email | 2 d | 48 tote bags, wants a price by Friday | Hey Sam, 48 totes one color comes to ... Want me to send a mockup? |

### Other replies waiting
None.
...
```

## Out of scope

Sending, scheduled or automatic runs, and other businesses' inboxes.
