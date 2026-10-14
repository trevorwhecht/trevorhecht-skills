---
name: trevskills-timecard
description: Use when the user pastes iMessage "Time in"/"Time out" timestamps (text or screenshot) and wants an Apple Calendar event logged for that work shift — e.g. "/trevskills-timecard" with a screenshot of the work-shift thread.
---

# Timecard

Turn pasted "Time in" / "Time out" timestamps into an Apple Calendar event.

## Parsing

- First timestamp in the input = shift start, last = shift end.
- Resolve relative dates against today: "Yesterday 5:59 PM" → yesterday's date. Bare times with no date → today.
- If the end time is earlier than the start time, the shift ran overnight — end date is the next day.
- Title: `<WORKER NAME> -<weekday>` (lowercase weekday of the **start** date). If the messages are clearly from someone other than <WORKER NAME>, use that name in the same format.

## Lunch / breaks

There is not always a lunch — never assume one. Only if the user mentions a lunch or break (e.g. "add a 30 min lunch at 5pm"), split the shift into **two events** around the break (same title on both) so the event durations sum to paid hours. If they give a break length but no start time, ask when it was.

## Always log

ALWAYS create the calendar event(s) for any new timestamps in the input — even when the user's message is a question (totals, pay, etc.). Answer the question AND log the shifts in the same turn. Pay rate for totals: set `PAY_RATE` below (default **$0.00/hr** — edit this line).

## Creating the event

Calendar: **"<CALENDAR NAME>"** (iCloud — exact name; the sidebar truncates it). Build dates field-by-field — never pass a date string to AppleScript (locale-fragile):

```bash
osascript <<'EOF'
set startD to current date
set year of startD to 2026
set month of startD to 9
set day of startD to 2
set time of startD to (12 * hours + 4 * minutes)
set endD to current date
set year of endD to 2026
set month of endD to 9
set day of endD to 2
set time of endD to (19 * hours + 36 * minutes)
tell application "Calendar"
	tell calendar "<CALENDAR NAME>"
		make new event with properties {summary:"<WORKER NAME> -wednesday", start date:startD, end date:endD}
	end tell
end tell
EOF
```

`time of` is seconds since midnight; `hours`/`minutes` are AppleScript constants (3600/60). Use 24-hour values.

## After creating

Report exactly what was created — title, date, start–end for each event — so a bad parse is obvious and the user can delete the event in Calendar.
