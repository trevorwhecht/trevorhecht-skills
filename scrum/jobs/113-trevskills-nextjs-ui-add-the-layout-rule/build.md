STATUS: READY
## Summary
Added 4 bullets to `nextjs/skills/trevskills-nextjs-ui/references/apple-hig.md`: Hero planes and One size contrast right after `Type scale`, Stacked text and Where these apply right after `Alignment`. No other file changed. Project has no test runner (Test/Typecheck/Lint: none), so each criterion was verified with the grep commands below.

## Acceptance criteria
1. Three planes bullet — verified by `grep -n -i 'plane' .../apple-hig.md` → line 9 `**Hero planes:** ... huge type at the back, the subject in the middle, the buttons on top` (and line 16) — PASS
2. One huge thing, rest small, no middle sizes, not contradicting Type scale — verified by `grep -n -i 'middle sizes' .../apple-hig.md` → line 10, which keeps the rest at body or caption size (sizes from the Type scale set) and says the fixed type scale still holds — PASS
3. Stacked text left aligned, not centred, grouped by closeness — verified by `grep -n -i 'centre' .../apple-hig.md` → line 15 — PASS
4. Applies to hero and marketing only; dashboard, table and form rules win; accent count unchanged — verified by line 16 text and `grep -c -i 'accent' .../apple-hig.md` → `1` — PASS
5. At most 8 added lines, file starts with `## Apple HIG Look Rules`, one file — verified by `git diff --stat` → `1 file changed, 4 insertions(+)` and `head -1` → `## Apple HIG Look Rules` — PASS

## Rulings
- Ruling: added new bullets beside Type scale and Alignment rather than rewriting the existing ones — keeps existing rules intact and the diff to pure insertions — cost if wrong: a reviewer may prefer merged wording; trivial to fold in.
- Ruling: no dashes or hyphenated words in the new lines (public copy, per the job hint) — checked with `git diff -U0 | grep '^+[^+]' | sed 's/^+- //' | grep -- '-\|–\|—'` → no matches (exit 1) — cost if wrong: none.
- Ruling: the Grouping bullet is sharpened by the Stacked text bullet (grouping by closeness) placed after Alignment instead of a separate line next to Grouping — Grouping (line 13) and Alignment (line 14) sit next to each other, so the new bullet is adjacent to both.

## Scrum map
- none

## Commits
- 969a16b trevskills-nextjs-ui: add hero planes, size contrast and stacked text layout rules
