---
name: trevskills-owa-feedback
description: Lists what feedback One With Arts (OWA) work still needs from Trevor, then walks him through the open items one at a time and saves each answer. Reads onewitharts/docs/feedback-needed.md. Use for /trevskills-owa-feedback, "what feedback do you need", "what do I owe you", "OWA feedback".
---

# OWA feedback

Shows what Trevor still owes Claude feedback on for One With Arts, then collects it one item at a time.
Only lists what the file says. Never invents an item.

## 1. Read

Open `~/Developer/repos/onewitharts/docs/feedback-needed.md` (one line per open item).
If the file does not exist, say "feedback-needed.md does not exist yet" in one line and stop.
Skip lines already marked done. If none are open, say "Nothing is waiting on you." and stop.

## 2. List

Print the open items as a short numbered list, oldest first. Each line: the item, then where it is used
(the file, page or feature the line names). No other prose.

## 3. Ask, one item at a time

Start with item 1. Ask only that item.
- When the answer is a pick between options, use AskUserQuestion with those options.
- Otherwise ask in plain chat and wait.

Move to the next item only after the current answer is saved. Trevor can say "skip" (leave the line open and go on)
or "stop" (end the run).

## 4. Save

Save his answer where the item line says it goes.
- A file in a repo: queue a scrum knowledge-save job, per the global CLAUDE.md "Save what I teach" rule.
  Never hand-edit the file.
- Mark the item done in `feedback-needed.md` through that same job, so the answer and the mark land together.
- When the line names no place to save, ask Trevor where it should go. Never guess.

## 5. Finish

After the last item, say how many were saved and how many are still open.
