---
name: trevskills-screenprint
description: Use when modelling, estimating or explaining garment screen-print production — presses, heads and pallets, flashes, underbase, mesh, conveyor dryers, cure times, prints per hour, setup time, manual vs automatic fit — in code, specs, reviews or questions for the shop. Also use when a term like PFP, wet-on-wet, index, platen, forced-air, discharge or revolution appears in a ticket.
---

# Screen print production

Domain reference for a print-shop management app. Every number in `reference.md` carries a source;
`(unverified)` and `(derived)` are marked. The shop's own answers are in reference.md §10 and win over
any published figure.

**Announce at start:** "Using trevskills-screenprint for the production rules."

## Rules that estimators get wrong without this

| Rule | Detail |
|---|---|
| Head budget (auto) | `screens + flashes + cooldowns ≤ heads` per revolution. Underbase is a screen. A flash takes a head on the shop's Brown AP-67J (6/7): 6 screens wet-on-wet only, 5 screens when one head flashes. UB screens count, so a dark 3-colour job is UB1 · flash · UB2 · 3 colours, with the cool-down only when a head is spare. |
| Underbase | Auto: two UB screens (UB, flash, UB2) or a second revolution at ≈ half speed. Manual: one screen, print-flash-print on the same platen. The shop's manual has no flash (only the AP-67J does), so a dark-garment manual job needs an external or borrowed flash, or the AP-67J, or is a no-flash single hit. |
| Dryer rate | `PPH = floor(beltWidth ÷ 14) × chamberLength × 3600 ÷ (dwell × 16)` (14 in garment on a 16 in pitch). Dwell ≈ 30 s plastisol, 75 s+ waterbased. Matches BBC's tables within ~4 %. Belt and chamber come from the shop's equipment record (seed catalog); a dryer with no dimensions and no entered rate has no computed rate. |
| Dryer gates ink | A dryer with no waterbased rate cannot cure waterbased or discharge. One belt speed per dryer: mixed inks run at the slowest. |
| Job rate | `min(press PPH, dryer PPH for that ink, crew rate)`. Shirts stack and wait when the dryer is the limit. |
| Real auto speed | 250–420 PPH solo, 500–850 with loader + catcher, on runs over 100. Makers claim 1,000+. Colour count slows a manual, not an auto. |
| Setup | `base + per screen`: ≈ 5 + 2–3 min/screen with pin registration, ≈ 45 min total without. Autos need an extra UB screen, so setup is longer than the manual's. |
| Manual vs auto | Break-even 50–72 pieces (shop: ≤ 50 → manual). Forced to manual: more heads than the press has, print bigger than the auto's platen, ink the auto's dryer cannot cure, odd garments (sleeves, bags, zippers). |
| Shop ink groups | Waterbased HSA, HSA+ (own underbase, no UB screen), LSA, discharge; plastisol Normal, Softhand. Discharge needs no underbase and the shop never flashes it. Details in reference.md §10. |
| Published PPH | Display only. Estimates use the shop's entered rates; a press with no rate falls back to the global model. |

## Where to read more

`reference.md` sections: 1 anatomy & vocabulary · 2 capacity rules · 3 underbase/ink/garment · 4 mesh ·
5 curing & dryer throughput · 6 throughput & setup numbers · 7 job-to-press fit · 8 electrical & air ·
9 glossary & manufacturers · 10 shop answers and open questions.

## Common mistakes

- Inventing a belt pitch or gap. Use the 14 in / 16 in constants above unless the shop gives others.
- Taking a maker's shirts-per-hour as a default rate.
- Letting a flash take a head on a manual press. In general a manual flash swings over a pallet and costs no head there; this shop's manual has no flash at all.
- Counting the second UB hit as free on an auto. It is a second screen or a second revolution.
- Suggesting a flash for discharge. The shop never flashes discharge.
- Asking the shop a §10 question that is already answered.
