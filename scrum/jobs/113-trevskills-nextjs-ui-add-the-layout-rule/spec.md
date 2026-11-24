# trevskills-nextjs-ui: add hero and stacked-text layout rules
UI surface: no
Hard stops: none
Human setup: none
Lane: fast
Complex: no

## Problem
Two reels Trevor sent (2026-11-20) gave three layout rules never added to the `trevskills-nextjs-ui` skill: three planes on a hero, one huge thing with the rest small, and left-aligned grouped stacked text. `apple-hig.md` already has related bullets (type scale, grouping, alignment, one accent colour), so the new rules must sharpen, not repeat.

## Scope
In: add about 3 to 5 short bullets, own words, to `nextjs/skills/trevskills-nextjs-ui/references/apple-hig.md`:
- Hero planes: big type at the back, the subject in the middle, buttons on top.
- One size contrast: one element huge, the rest small, no middle sizes (sharpen the `Type scale` bullet, do not contradict it).
- Stacked text: do not centre it, left align it, group by closeness: heading with its image, then price and button together (sharpen `Grouping` and `Alignment`).
- Marketing and hero pages only: say it does not apply to dashboards, tables or forms, where the existing table rules win.
Out: repeating the accent-colour rule; SKILL.md; any other file.

## Acceptance criteria
1. `grep -n -i 'plane' nextjs/skills/trevskills-nextjs-ui/references/apple-hig.md` shows the three planes bullet.
2. One huge thing, the rest small, no middle sizes, not contradicting `Type scale`.
3. `grep -n -i 'centre' ...apple-hig.md` shows stacked text left aligned, not centred, grouped by closeness.
4. New text says it applies to hero and marketing layouts and dashboard, table and form rules win; `grep -c -i 'accent' ...apple-hig.md` still returns 1.
5. At most 8 added lines; file still starts with `## Apple HIG Look Rules`; `git diff --stat` shows one file.

## Likely files
- `nextjs/skills/trevskills-nextjs-ui/references/apple-hig.md`
