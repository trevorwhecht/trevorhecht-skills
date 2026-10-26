# Screen Printing Production Knowledge Base (trevskills-screenprint reference)

Loaded from SKILL.md in this folder. Read the section you need, not the whole file.

Scope: garment screen printing PRODUCTION (press, flash, dryer, screens, scheduling), not art/design.
Purpose: give a coding agent enough domain logic to model jobs, presses, dryers and time estimates in a
print-shop management app. Every number has a source URL in the section's `Sources` list.
`(unverified)` = from memory/inference or a single weak source; confirm with the shop owner (see §10).
`[n]` = source index in that section.

Conventions used throughout:
- "Color" (in a press name) = print head. "Station" = pallet/platen. A "6/8" or "6x8" = 6 heads, 8 pallets.
- Temperatures are ink-film temperatures unless stated as dryer/oven setting.
- PPH = pieces (prints) per hour. "Dozen per hour" (doz/hr) is common shop talk: 40 doz/hr = 480 PPH.

---

## 1. Press anatomy and vocabulary

### Core parts
- **Head** = print assembly over one pallet position: screen clamps, squeegee, floodbar. A head can instead
  hold a flash unit. Press "color count" = number of heads, not inks you can actually use [1].
- **Station / pallet / platen** = the board the garment is loaded on. Station count = max garments on the
  press at once. Stations = heads + non-head stations (load/unload) [1].
- **Load / unload station** = station with no head. One shared station is enough for a single operator;
  separate load and unload stations speed up two-person crews [1].
- **Index** = the carousel rotating every pallet one position. Auto prints all heads simultaneously at each
  dwell, then indexes. Throughput of an auto is set by (index time + longest head dwell) per index, NOT
  by color count — more colors do not slow an auto (they do slow a manual) [2].
- **Revolution** = one full trip of a pallet around the carousel. Normal jobs: one revolution per garment
  (load → every head → unload). A **second revolution** (re-running some heads on the same garment) is a
  press program option, e.g. M&R "Revolver" sequencing: prints heads in a programmed order, allows multiple
  flashes without losing screen position [3][4]. Forum users describe "print white twice, flash, cycle back
  to that head", or "print, flash, reverse, print again" — slower than two screens, used when short of heads
  or staff [4].
- **Flash (flash cure / flash head)** = IR or quartz heater that gels a layer so the next ink can print on
  top. On an auto most flashes occupy a head position [1]. Some presses (Lawson Express-EX) can print and
  flash at the same station and run up to 3 flashes, so a flash does not always cost a color [5].
- **Cool-down station** = an empty head (or fan) after a flash so the hot underbase cools before the next
  screen; prevents ink build-up on the back of following screens [6][1].
- **Print-flash-print (PFP)** = print a layer, flash, print again (same image). On a manual = same screen
  twice. On an auto = two screens on two heads, or a second revolution (see §2).
- **Wet-on-wet** = printing colors one after another without flashing between them. Order: lightest to
  darkest, smallest ink footprint first. A flashed underbase must be done before the wet-on-wet colors [6].
- **Off-contact** = gap between screen mesh and garment at rest. 1/16"–1/8" for tees; double for hoodies and
  fleece [7]. Higher off-contact = cleaner snap-off [6]. Practitioner: 1–3 cm reported on an auto (likely
  meant mm) [8] `(unverified units)`.
- **Flood stroke / print stroke** = floodbar fills the stencil with ink (no pressure); squeegee stroke pushes
  ink through. Autos have separate, programmable flood and print speeds/pressures (e.g. ROQ "AC servo motor
  /flood strokes") [9].
- **Squeegee durometer** = blade hardness (Shore A). Range 40–80; 60–70 and triple 70/90/70 most common.
  70 = workhorse; 60 = soft, heavier deposit, low mesh, specialty (puff, high density, glitter);
  70/90/70 = halftones, fine line [10]. Higher durometer → less ink deposit [6].
- **Squeegee angle**: sources use opposite reference planes. One cites 65°–75° optimal (measured from the
  screen); another frames "low angle ~45° = more deposit, high angle ~0° = sharper" [10]
  → store angle with its convention, or don't model it.
- **Print pressure** (auto, pneumatic): 40–60 psi reported by one practitioner [8].
- **Micro registration** = fine X/Y/rotation knobs per head. **Pin/registration systems** (Tri-Loc, Shurloc,
  ROQ pin) pre-register screens off-press.

### Manual vs automatic
| Aspect | Manual | Automatic |
|---|---|---|
| Who moves | Operator rotates heads/platens, pulls every stroke | Motor/air indexes; squeegees driven |
| Heads | Typically 1–8 colors, 1–8 stations; often "all heads down" (colors = stations) [1] | Always more stations than colors [1] |
| Flash | Swing-over flash, operator times it (seconds); the shop's manual has no flash (see §10) | Flash occupies a head; timed per index |
| Consistency | Varies with operator fatigue | Same stroke every time → can use higher mesh, even deposits [11] |
| Crew | 1 per press [2] | 2 typical at speed (loader + unloader/catcher) [2]; 3 recommended (load, unload, watcher) [12] |
| Speed | 40–100 PPH [2] | 500–800 PPH sustainable [2] |
| Price (2010s) | ~$1k–$5k [2][13] | entry ~$34k [2]; $20k–$100k [13] |
| Utilities | None (except flash) | Electric + often compressed air (§8) |

### Sources
1. https://anatol.com/blog/which-screen-printing-press-configuration-is-the-best-fit-for-your-screen-printing-shop
2. https://www.rushordertees.com/blog/manual-vs-automatic-screen-printing-machine/
3. https://www.mrprint.com/equipment/sportsman-ex-automatic-screen-printing-press
4. https://theshirtboard.com/index.php/topic,12637.30.html (forum: Revolver usage)
5. https://www.lawsonsp.com/products/express-ex-automatic-screen-printing-press
6. https://anatol.com/blog/how-to-save-time-with-wet-on-wet-screen-printing-on-your-automatic-press
7. https://www.screenprinting.com/blogs/news/everything-you-need-to-know-to-screen-print-an-underbase
8. https://theshirtboard.com/index.php/topic,11051.15.html (forum: set-up times thread)
9. https://kolormatrix.com/roq-print-you.html
10. https://screenprinting.com/blogs/news/squeegee-durometer-angle-deep-dive-with-colin ; https://www.printablepress.com/screen-printing-squeegee-guide/
11. https://anatol.com/blog/finding-the-right-mesh-count-the-impact-of-your-screen-printing-press
12. https://theshirtboard.com/index.php/topic,4360.msg48315.html (forum: one-man shop goes auto)
13. https://thrivescreenprinting.com/automatic-vs-manual-screen-printing-press-in-phoenix

---

## 2. Capacity rules (what fits on a press)

### The head budget (auto)
Every head is one of: **print screen**, **flash**, **cool-down (empty)**. Stations without heads are
load/unload. So for a C-color / S-station auto:

```
usable_print_screens = C - flashes - cooldowns           (heads are the constraint)
load_unload_stations = S - C                              (usually 1 or 2)
required_heads(job)  = screens + flashes + cooldowns
fits(job)            = required_heads(job) <= C            (single revolution)
```

- Anatol: underbase needs its own head; most flashes need a head; may need another head as cool-down.
  "A 3-color job on black requires at least 5 heads" (UB + flash + 3 colors, no cool-down) [1].
- Anatol: a 4-color press can't do 4-color process "under most circumstances" [1].
- Worked example quoted by a search summary: "a 6×8 with one flash/cool is now a 4 color 8 station" [2]
  (UB counted as one of the 4? — ambiguous; see below).
- Printing.org/Workhorse: a 6-color design + 1 flash + cool-down needs 8 heads [3].
- Exception: presses that flash at a print station / between heads (Lawson Express-EX, up to 3 flashes)
  don't lose a head per flash [4]. Brown ElectraPrint Jr has "quartz flash ports on each head" [5] → model
  per press whether flash consumes a head (`flashUsesHead: boolean`).

### Why a 6/7 runs "5 screens + 1 flash" (not 6 colors) on darks
- 6/7 = 6 heads, 7 stations → 1 load/unload station, 0 spare heads.
- A dark-garment job needs a flashed underbase → one head becomes the flash → 5 heads remain for screens.
- Those 5 screens = underbase + 4 top colors (no cool-down), or UB + 3 colors + cool-down.
- Only wet-on-wet (no flash at all, e.g. light garment or no underbase) uses all 6 heads as colors [1][6].
- Some top colors (yellow, gold) are thin and cover poorly over a single UB hit; shops re-flash or print
  them last [6] → costs another head.

### Common configurations (dark garment, plastisol, 1 flash)
| Press (heads/stations) | Max top colors, UB + flash, no cool | with cool-down | wet-on-wet only (no UB) |
|---|---|---|---|
| 4/5 | 2 | 1 | 4 |
| 6/7 | 4 | 3 | 6 |
| 6/8 | 4 | 3 | 6 |
| 8/10 | 6 | 5 | 8 |
| 10/12 | 8 | 7 | 10 |
Formula: top_colors = C − 1 (UB) − flashes − cooldowns. Double-hit UB (two UB screens) costs one more head.
(Table derived from rule in [1]; `(derived)`.)

### Underbase: one screen on a manual, two on an auto
- Manual: print UB, swing flash over the same platen, print UB again with the SAME screen (PFP). The platen
  never leaves the head, so one screen does both hits. In this shop the manual has no flash (see §10): a
  manual PFP needs an external or borrowed flash, or the AP-67J, or is a no-flash single hit.
- Auto: a pallet visits each head once per revolution. A second UB hit after the flash must come from a
  different head → a second, identical UB screen ("UB1, flash, UB2") — or a second revolution via a
  sequencing program (Revolver) at a speed penalty [7][8].
- Typical auto dark-garment sequence: `UB1 → flash → (cool) → UB2 or highlight → top colors wet-on-wet →
  highlight white last`. Forum standard: "PFPF the base, then print the top colours" [9].
- Counter-view: Ryonet says don't PFP a white underbase (thicker, cure/adhesion problems); one pass with a
  sharp squeegee or a double stroke is usually enough [10][11]. → shop-specific (§10).

### When a second revolution is used
- Not enough heads for screens + flashes (e.g. 2 flashes needed on a 6-head press) [7][8].
- Small jobs where pulling an extra screen costs more than the speed loss [8].
- Effective rate ≈ single-rev rate ÷ revolutions (each garment occupies a pallet for 2 trips) `(derived)`.

### Front + back, sleeves
- Each location is a separate press run (separate setup) unless two presses feed one dryer (front on press
  A, back on press B as garments come off the dryer via a return belt) [12].

### Sources
1. https://anatol.com/blog/which-screen-printing-press-configuration-is-the-best-fit-for-your-screen-printing-shop
2. https://screenprinting.com/blogs/news/choose-right-automatic-press (via search summary; not fetched)
3. https://printing.org/content/2020/01/10/workhorse-offers-cutlass-se-mid-level-six-color-eight-station-automatic-press (via search summary)
4. https://www.lawsonsp.com/products/express-ex-automatic-screen-printing-press
5. https://impressionsmagazine.com/products/electraprint-junior-series/29620/
6. https://theshirtboard.com/index.php/topic,17177.0.html
7. https://www.mrprint.com/equipment/sportsman-ex-automatic-screen-printing-press
8. https://theshirtboard.com/index.php/topic,12637.30.html
9. https://theshirtboard.com/index.php/topic,14697.0.html
10. https://www.screenprinting.com/blogs/news/everything-you-need-to-know-to-screen-print-an-underbase
11. https://support.solutionsforscreenprinters.com/hc/en-us/articles/36424146390804-How-to-Properly-Print-a-White-Base-Underbase-Screen
12. https://www.printing.org/content/2022/12/21/new-vastex-econored-vi-series-dryers-cure-up-to-2-700-garments-per-hour (Vastex return-belt note, via search summary)

---

## 3. Underbase, ink and garment logic

### When an underbase is needed
- Rule: ink color lighter than the garment (or any bright/vivid color on a dark) → white underbase.
  "If you think you need an underbase, you probably do" [1].
- No UB: dark ink on light garment, or tonal designs where dulling is acceptable.
- UB adds: 1 screen (2 on auto if double-hit), 1 flash, usually a highlight white on top → +2–4 heads.
- Mesh for UB: 110–160; 180–200 for fine detail [1] (more in §4).

### Discharge (the exception to underbasing)
- Discharge removes garment dye instead of covering it → no UB, no flash, soft hand.
- Works only on 100% natural fibers dyed with dischargeable (direct, not reactive) dyes; "only 100% natural
  fabric colored with selected dyes discharge well" [2]. Won't discharge polyester or nylon [3].
- Agent = zinc formaldehyde sulfoxylate (ZFS); test at 4/6/8%, max 8% [2]. Activator added last [3].
  Mixed discharge has a limited pot life `(unverified: commonly 4–8 h after activation; check TDS)`.
- Reaction: >180°F with water present; best below 250°F; binders need ~300°F to crosslink [2].
- Results vary by dye lot → scheduler should flag discharge jobs for a test print.
- Formaldehyde: wash or tag goods [3]. Safety: SO2 PEL 2 ppm 8-h [2].

### Polyester / blends: dye migration (bleed)
- Poly dyes sublimate and migrate into plastisol between 280°F and 320°F [4]. Low-cure inks (190°F–300°F
  fusion) are the fix; aim ink film 290°F for 5–8 s, not 5° over [4].
- Flash on poly: ink surface 180°F–200°F for 2.5–3.5 s; platen 140°F–160°F; ≥220°F surface → blistering /
  immediate bleed [4].
- **Grey vs white underbase**: grey "blocker" (carbon/barrier) underbases stop dye migration; white alone
  doesn't. Grey must also be low-cure or the advantage is lost [4]. Examples: Monarch ULT Shield Grey 270°F
  [5]; TRQ Low Bleed Barrier Grey 290–300°F, 86–155 mesh, 25–35 N/cm [6]; Barrier Black 260°F [7].
- Low-cure poly white example: Wilflex Epic Top Score LC White cure 260°F–280°F, flash 220°F, 86–230 mesh [8].
- Scheduler rule: garment fiber contains polyester → require low-cure/low-bleed ink set + blocker UB on
  colored poly; lower dryer temp → longer dwell or slower belt (§5).

### Flash temperatures and dwell (per ink type)
Anatol survey of ink makers (quartz flash) [9]:
| Ink | Flash/gel temp °F | Quartz dwell s |
|---|---|---|
| Standard plastisol | 220–250 | 2.5–4.0 |
| Fast-flash plastisol | 190–210 | 2.0–3.5 |
| Water-based | 220–250 | 3.5–5.5 |
| Discharge | 190–220 | 4.5–7.0 |
| Silicone | 170–210 | 4.0–6.0 |
- Starting settings: plastisol/cotton 2.5 s at max intensity or 3.5 s at intensity 4; poly/nylon 2 s at
  intensity 4; WB/silicone 3.5–4 s at intensity 4 [9].
- Pallet preheat 120°F–160°F [9].
- Ink maker examples: Wilflex Epic Rio colors flash 220°F 3–5 s, cure 266–320°F [10]; Epic Matte Black flash
  160°F 3–5 s, cure 320°F [11]; Epic Quick White flash 220°F, cure 300°F [11].
- Conflicting: Printable Press gives plastisol gel 240–270°F surface [12].
- Gel target = tacky but not smudging; a fully cured UB hurts adhesion of next colors [13].
- IR (panel) flashes on manuals are slower than quartz; manual flash dwell is longer `(unverified:
  typically 5–15 s for an 18x18 IR flash over a UB; shop-specific)`.
- Flash height 1.5–2" above shirt (double for hoodies) [1].
- Lawson: dark-garment manual PFP shops report ~30 PPH vs much more without flash [14].

### Sources
1. https://www.screenprinting.com/blogs/news/everything-you-need-to-know-to-screen-print-an-underbase
2. https://www.printing.org/detail/resource/Understanding-Discharge
3. https://screenprinting.com/products/ryonet-discharge-base ; https://cn.avient.com/node/9721 (via search summary)
4. https://avient.com/node/9723 (PolyOne/Avient "Printing Performance Wear Tips")
5. https://impressionsmagazine.com/news/monarch-launches-two-new-plastisol-inks/28643/
6. https://kolormatrix.com/products/trq-lb-barrier-grey
7. https://www.screenprinting.com/blogs/news/how-to-screen-print-on-polyester-with-a-blocker-base
8. https://cn.avient.com/sites/default/files/2022-10/2200%20EPIC%20TOP%20SCORE%20LC%20WHITE_ENG_V3.02.pdf (via search summary)
9. https://anatol.com/blog/a-general-guide-to-quartz-flash-settings-for-screen-printing
10. https://www.screenprinting.com/products/wilflex-epic-rio-red-plastisol-ink
11. https://screenprinting.com/products/wilflex-epic-matte-black-plastisol-ink ; https://screenprinting.com/products/wilflex-epic-quick-white-plastisol-ink
12. https://www.printablepress.com/how-to-use-flash-dryer-screen-printing/
13. https://www.printablepress.com/how-to-screen-print-on-dark-shirts/
14. https://lawsonsp.com/blogs/plastisol-ink-support-articles/eliminate-flash-curing-do-i-really-need-it (via search summary)

---

## 4. Mesh counts

Notation: US mesh = threads per inch (TPI). Second number = thread diameter in microns, e.g. "200-45" =
200 TPI, 45 µm [1]. Standard thread ~60–70 µm; thin thread 35–45 µm [1]. Euro: threads/cm, "43-90 T" ≈
110 TPI... "120/305" = 120/cm ≈ 305 TPI [2][3]. S/T suffix (old Euro thread class: S = small, T = medium,
HD = heavy) `(unverified)`.
- Thin thread → bigger openings, more open area at same count: 305/40 µm = 25% open vs 305/35 µm = 33% [2].
  Thin-thread 135 holds detail ~156 but lays ink like ~110; popular for whites/UB; pops more often [1].
- Rule of thumb: thick ink → lower mesh; thin ink → higher mesh [4].
- Halftone rule: max LPI ≈ mesh ÷ 4.5 (230 → ~51 LPI) `(forum rule of thumb)` [5].
- 156 is now sold as 158 by some vendors [5].

### Typical mesh by use
| Use | Mesh (TPI) | Notes / source |
|---|---|---|
| White UB, manual | 110–160 | [6]; 110 = one pass coverage [5]; 156 common [4] |
| White UB, auto / sim process | 156–230 (UB), 200–230 for CMYK UB | autos tolerate higher mesh due to consistent stroke [7][8] |
| UB, fine detail | 180–200 | [6] |
| Highlight white | 200–230 | [8] |
| Plastisol top colors (spot) | 156–230 | 230 ok on top colors/detail; 230 not advised for plastisol where opacity needed [4] |
| Sim process top colors | 230–305 | forum: auto UB 230, tops 230/305; manual UB 156, tops 305 [8][9] |
| Fine halftones / 4CP | 230–305 (355 for 65+ LPI) | [5] |
| Water-based | 156–230 typical; 110–225 TPI range (Permaset Aqua) | 156 can over-deposit and bleed [4]; forum: 156–160 for HSA white, 200–230 for RFU [10] |
| Discharge | 110–230; 110 or 156 for discharge white [5]; Matsui Alpha 110–230 [10] | thin ink → 230 also common [5] |
| Specialty (puff, glitter, HD) | low mesh, 60-dur squeegee | [11] (exact counts unverified: glitter 40–86) |
| Poly blocker grey | 86–155 | [12] |

### Tension
- 25 N/cm = "good" (Ryonet) [13]. Ranges by mesh: 15–20 N/cm (40–86), 20–25 (110–160), 25–30 (200–305) [14].
  25–35 N/cm general production; 30–40 halftones [14]. Forum: ≥20 N/cm minimum, benefits up to ~35 [15].
- Practitioner on auto: "mid 20s or better" [16].
- Static frames lose tension over time; retensionable (roller) frames can be re-tightened `(general)`.

### Sources
1. https://www.printavo.com/blog/mech-cheat-sheet/
2. https://screenprintingmag.com/?p=3261 (via search summary)
3. https://www.scribd.com/document/563486508/Sefar-Basic (via search summary)
4. https://graphics-pro.com/education/how-does-the-recommended-mesh-count-differ-between-plastisol-and-water-based-inks/
5. https://kolormatrix.com/blogs/news/understanding-screen-printing-mesh-count-why-110-156-230-amp-305-mesh-print-differently (via search summary)
6. https://www.screenprinting.com/blogs/news/everything-you-need-to-know-to-screen-print-an-underbase
7. https://anatol.com/blog/finding-the-right-mesh-count-the-impact-of-your-screen-printing-press
8. https://ultraseps.com/film-positive-output-settings.pdf (via search summary)
9. https://theshirtboard.com/index.php/topic,18009.0.html
10. https://theshirtboard.com/index.php/topic,25680.0.html ; https://kolormatrix.com/products/matsui-alpha-series-ready-for-use-water-base-or-discharge-ink
11. https://screenprinting.com/blogs/news/squeegee-durometer-angle-deep-dive-with-colin
12. https://kolormatrix.com/products/trq-lb-barrier-grey
13. https://help.screenprinting.com/en-US/whats-considered-good-mesh-tension-16558
14. https://www.printablepress.com/how-to-stretch-re-tension-screen-printing-mesh/ (via search summary)
15. https://theshirtboard.com/index.php/topic,5984.msg66380.html
16. https://theshirtboard.com/index.php/topic,11051.15.html

---

## 5. Curing and dryer throughput

### Cure targets
- **Plastisol**: entire ink film (not surface) to fusion temp, typ. 320°F [1][2]. Some 300°F (Epic Quick
  White) [3]; low-cure 260–280°F [4]; range 266–320°F (Epic Rio) [5]. Thick deposits (HD) take longer [2].
  Vendor: 320°F for at least 1 min (dryer dwell) [1]. Practitioner: 30 s dwell on a 60-s-guideline ink →
  cracking; "double your dwell" [6].
- Laser/IR guns read surface; can be off 120–150°F early in the cycle → use donut probe / temp strips [3][6].
- **Water-based**: water must fully evaporate before ink reaches cure temp, then hold ≥20 s [7].
  Permaset: 2–3 min at 320°F ink temp [8]. Green Galaxy HSA: ideally 3 min at 300–320°F, min 90 s at 360°F;
  low-cure catalyst (Warp Drive) 1.5% by weight, cures as low as 180°F after 48 h, 24-h pot life [9].
- **Discharge**: binders crosslink ~300°F; <1 min over 320°F in principle, but "a minimum of 90 seconds in
  the oven is recommended; some systems require a minimum of 3 minutes" [10]. Ryonet: hold ≥320°F
  20–30 s; can take ~3 min in dryer [11]. Heat press discharge 320–350°F 10 s; <330°F to protect some reds [10].
- **Oven variation**: dryer temps vary 30°F+ over time and up to 50°F with belt loading [10].
- **Forced air vs IR**: WB/discharge cure needs airflow to carry moisture out; IR alone is inefficient,
  longer dwell partly compensates but not at commercial volume [12]. Best WB dryer = flash zone + longer
  cure zone [13]. Gas dryers dominate at high volume (e.g. M&R Sprint 2000) [14].

### Dryer throughput formula (validated against BBC published rates)
```
belt_speed (in/min)   = heated_chamber_length (in) / dwell (min)
across                = floor(usable_belt_width / garment_footprint_width)
pph                   = across * belt_speed * 60 / garment_pitch (in, along belt)
                      = across * chamber_length * 3600 / (dwell_s * pitch)
```
Check — BBC Forced Air Conveyor, 48" chamber, 24" belt [15]:
- Plastisol 25 s, 12"x18" footprint: across = 2 → 2 × 48 × 3600 / (25 × 18) = **768** → published **750**.
- Same, 18"x18" footprint: across = 1 → 384 → published **400**.
- Water-based 45 s, 12"x18": 2 × 48 × 3600/(45 × 18) = 427 → published **425**.
- 36" belt model, plastisol 25 s, 12x18: across = 3 → 1152 → published **1150** [15].
→ The formula reproduces manufacturer tables within ~4%. Footprint = garment-as-laid (width × pitch), not
image size. Leave a gap factor; operators don't load perfectly `(calibration knob)`.

Heated-chamber length, not total belt length, is what matters; extensions (in/out-feed) add staging space
only [15][16]. Vastex: adding heat chambers raises capacity in direct proportion [16].

### Published dryer rates (plastisol vs water-based)
| Dryer | Belt | Chamber | Plastisol PPH | WB PPH | WB/plast ratio | Source |
|---|---|---|---|---|---|---|
| BBC Forced Air 8' | 24" | 48" | 750 (25 s) | 425 (45 s) | 0.57 | [15] |
| BBC Forced Air 10' | 36" | 48" | 1150 | 640 | 0.56 | [15] |
| BBC Aeolus | 36" | — | 1440 (30 s) | 960 (45 s) | 0.67 | [17] |
| Aeolus-class 12' | 54" | — | ~1900 (30 s) | 1280 | 0.67 | [18] |
| BBC Big Buddy 8' | 24" | — | 250–275 | — | — | [17] |
| BBC Little Buddy | — | — | 100+ | — | — | [17] |
| Vastex Little Red X1 | 24"–30" | — | ≥130 | ≥45 | 0.35 | [19] (AI-written listing) |
| Vastex Little Red X2-30 | 30" | (66" belt) | 260 | 90 | 0.35 | [20] |
| Vastex Little Red X3D-30 | 30" | 41" | 360 | 185 | 0.51 | [21] |
| Vastex EconoRed II-30 | 30" | — | 300 | — | — | [22] |
| Vastex EconoRed VI-30 / -54 / -78 | 30/54/78" | — | 900 / 1800 / 2700 | 300 / 600 / 900 | 0.33 | [23] |
| M&R Sprint 2000 (gas) | 48–72" | 12–16' | >2000 | 1600 | 0.8 | [14] forum |
- **Why WB ~halves throughput**: WB needs ~1.8× (BBC 25→45 s) to ~3× dwell to evaporate water before cure;
  same chamber → belt runs proportionally slower → PPH drops by dwell ratio. Observed WB/plastisol ratio
  0.33–0.67 across vendors (forced-air units are better: 0.56–0.67; IR-only small units 0.33–0.35).
- Practitioner: "40 dozen [480] an hour without cure problems with plastisol" on their dryer [24].

### Presses per dryer; bottlenecks
- Size dryer ≥ sum of PPH of all presses feeding it, at the slowest ink in use; leave margin [18].
- Mixed-ink problem: one dryer has one belt speed/temperature → a WB job and a plastisol job on two presses
  sharing a dryer force the dryer to the WB setting (or the plastisol press waits) `(derived)`.
- Two presses can share a dryer as front/back pair via return belt [16]; long infeed allows staging multiple
  printers around the dryer [18].
- When dryer is the bottleneck: press output > dryer PPH → operator slows/pauses press, or stacks printed
  goods (only possible after a full cure — wet prints can't be stacked) → effective job rate =
  min(press_pph, dryer_pph_for_ink, crew_load_rate) `(derived)`.
- Manual-shop dryers: entry dryers (100–300 PPH plastisol) easily keep up with 1–2 manuals (40–100 PPH each)
  but cap WB to 45–185 PPH [19][20][21].

### Sources
1. https://mclogan.com/blogs/news/how-to-properly-cure-plastisol-ink (via search summary)
2. https://lawsonsp.com/blogs/education-and-training/cure-plastisol-inks (via search summary)
3. https://screenprinting.com/products/wilflex-epic-quick-white-plastisol-ink
4. https://cn.avient.com/sites/default/files/2022-10/2200%20EPIC%20TOP%20SCORE%20LC%20WHITE_ENG_V3.02.pdf (via search summary)
5. https://www.screenprinting.com/products/wilflex-epic-rio-red-plastisol-ink
6. https://theshirtboard.com/index.php/topic,26617.0.html
7. https://help.screenprinting.com/en-US/how-do-you-cure-water-based-ink-136635
8. https://mclogan.com/blogs/news/how-to-properly-cure-water-based-inks (via search summary)
9. https://greengalaxy.ca/products/green-galaxy-cosmic-pink-water-based-ink ; https://greengalaxy.ca/products/green-galaxy-warp-drive-low-cure-additive
10. https://www.printing.org/detail/resource/Understanding-Discharge
11. https://www.screenprinting.com/products/ryonet-discharge-agent (via search summary)
12. https://bchtechnologies.com/blogs/blog/navigating-the-transition-to-waterbased-ink-printing
13. https://www.screenprinting.com/blogs/news/what-is-water-based-ink
14. https://www.theshirtboard.com/index.php/topic,26720.0.html ; https://theshirtboard.com/index.php/topic,3389.15.html ; https://www.vavato.com/en/l/2016-m-r-sprint-200-textieldrukmachine-%282x%29-A3-34606-3333
15. https://assets.stahls.com/stahls/content/pdf/techsheets/Forced-Air-Conveyors-Application-Sheet.pdf (BBC; text extracted and arithmetic checked)
16. https://www.printing.org/content/2022/12/21/new-vastex-econored-vi-series-dryers-cure-up-to-2-700-garments-per-hour
17. https://mclogan.com/products/aeolus-forced-air-dryer ; https://gjs.co/bbc-big-buddy-conveyor-dryer ; https://gjs.co/bbc-little-buddy-conveyor-dryer
18. https://lawsonsp.com/blogs/education-and-training/top-10-questions-when-shopping-for-a-conveyor-dryer (via search summary)
19. https://www.exapro.com/vastex-little-red-x1-p251201213/
20. https://kolormatrix.com/products/little-red-x2-series-30-x-5-5-dryer
21. https://kolormatrix.com/vastex-little-red-x3d-series-30-x-7-4-dryer.html
22. https://www.worklinestore.com/storage/allegati_prodotti//prodotto_1321_all_144_er-ii_1019.pdf
23. https://www.printing.org/content/2022/12/21/new-vastex-econored-vi-series-dryers-cure-up-to-2-700-garments-per-hour
24. https://theshirtboard.com/index.php/topic,4360.msg48315.html

---

## 6. Throughput numbers

### Manual press (one operator unless noted)
| Scenario | PPH | Source |
|---|---|---|
| General manual range | 40–100 | [1] |
| Entry manual, 1 employee | ~60 | [1] |
| 1-color, light shirt, dark ink | 60–100 skilled; 100–120 typical claim | [2] |
| 1-color, "2 a minute" | ~120 | [3] forum |
| Pessimistic 1 min/shirt incl. load/pull/stack | ~60 | [3] forum |
| Dark shirt, PFP white (print-flash-print) | ~30 | [4] Lawson |
| Multi-color with flash, 1 person | 20–40 `(inferred)` | from [4] + [1] |
| Manual, 3 operators | 350+ (ink/image dependent) | [3] forum |
| 30–50 s per shirt per operator | 72–120 | [5] |
- Two people on two manuals for an hour ≈ 120 prints [1].
- Job anecdotes: 700 shirts 1c front + 1c back, 2 people, <2 days incl. art + screens [3]; ~1,100 shirts in 2
  days, 2 people, M&R Chameleon [3].
- Manual registration drifts: check every 10–20 shirts [6].

### Automatic press
| Scenario | PPH | Source |
|---|---|---|
| Sustainable pace, 2-person crew | 500–800 | [1] |
| Entry auto, 2 employees | ~500 | [1] |
| One-man auto shop "when going good" | 250–400; don't expect 500 on every job | [7] |
| Solo loader/unloader (forum) | ~350; 420 ±12; 264 "once around with flash, average job"; 150–200 | [8] |
| With dedicated unloader/catcher | ~450 (couple of hours), ~420 after 3.5–4 h | [8] |
| Pro shop, runs >100 pcs | 850 typical, some 950; <700 flagged as problem | [8] |
| Same pro shop averaged over 3 days *incl. setups* | ~550/press, 6.5 setups/press/day, avg order 190 | [8] |
| Shop w/ loader+catcher, avg order 75 | ~230 avg; ~1,400/day in ~6 h printing | [8] |
| Long runs, fast operator | 4,000/day normal; 6,000+/day briefly | [8] |
| ROQ Eco customer | 600 → ~800 | [9] |
| Records | 1,264 (RushOrderTees 2010); 2,139 (M&R 2013, with unloader) | [1][10] |
- **Manufacturer claims**: ROQ YOU "up to 1,000 PPH" [11]; ROQ Fit "+1,000" [12]. Real sustained output with
  setups ≈ 25–55% of claim on short-run work; ~80–95% only on long runs with full crew `(derived from [8])`.
- **Left-chest prints run faster than a 14"-tall print** (shorter stroke) [8].
- Brown ElectraPrint Jr (closest match to "AP67jr"): no published PPH found; all-electric, 4–8 colors,
  20"x24" frames, quartz flash ports each head [13]. "AP67jr" model name not found in any source `(unverified)`.

### Setup time (press: empty press → first good shirt)
| Context | Time | Source |
|---|---|---|
| General vendor range, mount + align | 15–45 min/job (manual longer), + 15–30 min test prints | [14] |
| Auto with pin/CTS registration | 45 → 10–15 min/job | [15] |
| Registration system saves | 10–25 min/job on multicolor | [16] |
| Aspirational shop goal | ~5 min per screen | [17] forum |
| 6-color job, solo w/ micros | 15–20 min (spot on ~75% of the time) | [18] forum |
| 5-color, Tri-Loc pin | 5–6 min (excl. squeegees/ink) | [18] |
| 5–6 color, no registration system | 30–45 min | [18] |
| 8-color, 4-person team, no reg system | 20 min | [18] |
- Model as `setup_min = base + per_screen × screens`, e.g. auto with pins ≈ 5 + 2–3/screen; auto without pins
  ≈ 10 + 5–7/screen; manual ≈ 5 + 3–5/screen `(derived; calibrate per shop)`.

### Screen-making (per screen)
- Emulsion coat dry: 1–2 h in drying cabinet [19].
- Exposure: LED high output 18 s; LED 30 s; UV-blacklight 4:14 (230 yellow, 2/1 coat, Vastex units) [20];
  older fluorescent ~20 min; LED 3–6 min in same workflow [21]. Screens/hour: 3 → 10 with LED; conventional
  3–12/h vs ~50/h fast LED [21].
- Washout + dry + tape/block-out `(unverified: 5–15 min hands-on/screen)`.
- Reclaim (teardown side): pressure wash ~1.5 min/screen + de-haze + rinse; 10 screens in ~15 min by pressure
  washer vs ~20 min/screen hand scrubbing; remover dwell 10 s–1 min (EPA) up to 3 min (haze remover);
  5–6 gal water/screen [22].
- Press teardown (pull screens, scoop ink, clean squeegees/floodbars): no source found `(unverified:
  1–3 min/screen)`.

### Sources
1. https://www.rushordertees.com/blog/manual-vs-automatic-screen-printing-machine/
2. https://printify.com/blog/how-long-does-it-take-to-print-a-shirt/ ; https://www.yoprint.com/time-to-screen-print-100-shirts/ (via search summary)
3. https://theshirtboard.com/index.php/topic,10522.0.html
4. https://lawsonsp.com/blogs/plastisol-ink-support-articles/eliminate-flash-curing-do-i-really-need-it (via search summary)
5. https://ecommercefastlane.com/how-long-does-it-take-to-print-a-shirt-the-2026-definitive-guide-to-production-speed/ (via search summary)
6. https://www.printablepress.com/manual-vs-automatic-screen-printing-press/ (via search summary)
7. https://theshirtboard.com/index.php/topic,4360.msg48315.html
8. https://theshirtboard.com/index.php/topic,26917.0.html
9. https://blog.screenprinting.com/roq-eco-faster-index-speed/ (via search summary)
10. https://impressionsmagazine.com/news/mr-screen-printing-press-helps-set-world-record/20164/
11. https://kolormatrix.com/roq-print-you.html
12. https://screenprinting.com/products/roq-fit-automatic-screen-printing-press
13. https://impressionsmagazine.com/products/electraprint-junior-series/29620/
14. https://printify.com/blog/how-long-does-it-take-to-print-a-shirt/ (via search summary)
15. https://impressionsmagazine.com/process-technique/upgrading-to-an-auto-press/34973/ (via search summary)
16. https://screenprintingmag.com/?p=2599 (via search summary)
17. https://theshirtboard.com/index.php/topic,21660.0.html (via search summary)
18. https://theshirtboard.com/index.php/topic,11051.15.html
19. https://innovationstudio.unl.edu/sites/unl.edu.research.nebraska-innovation-campus.innovation-studio/files/media/file/SOP_Screen_Printing.pdf
20. https://kolormatrix.com/catalog/product/view/id/156 (via search summary)
21. https://impressionsmagazine.com/?p=16604 ; https://nxtbook.com/nxtbooks/impressions/201403/index.php?startid=69 (via search summary)
22. https://theshirtboard.com/index.php/topic,19726.0.html ; https://19january2021snapshot.epa.gov/sites/static/files/2014-01/documents/screen_printing_bulletin_1.pdf ; https://www.printablepress.com/how-to-reclaim-screen-printing-screen/

---

## 7. Job-to-press fit rules (scheduler)

Evaluate each press for a job; reject on hard constraints, then rank by estimated total time/cost.

### Hard constraints
1. **Head count**: `screens + flashes + cooldowns <= heads` (single revolution) — §2. Allow
   `revolutions = 2` only if the press supports sequencing (M&R Revolver etc.) and apply speed ÷ 2.
2. **Flash availability**: dark garment / UB job needs a flash unit on (or available for) that press; count
   flash units owned per press. The shop owns one flash, the AP-67J built-in; none for the manual (§10).
3. **Image size ≤ press max print area** (and screen frame fits). Examples: M&R Sportsman EX 4045 = 16"x18",
   5050 = 20"x20" (page overview also mentions 20"x28") [1]; ROQ YOU 16"x20" [2]; Brown ElectraPrint Jr
   20"x24" frames [3]; MHM Matrix 20x28 / 28x40 / 31x40 [4].
4. **Oversize / all-over** → requires oversize/AOP pallets; on some presses an AOP pallet takes 2 stations
   (Vastex on 8/10 color) [4]. Manual presses often have larger platens available `(unverified)`.
5. **Sleeves / pockets / legs** → special platens: Ryonet dual sleeve 2× 3.75"-wide areas for 23x31 screens on
   ROQ [5]; Lawson pocket/sleeve platen 3.5"x9" [6]. Track platen inventory per press.
6. **Air**: pneumatic autos require a running compressor (§8); all-electric autos (Brown ElectraPrint, ROQ E)
   don't [3][7].
7. **Dryer–ink compatibility**: WB/discharge need forced air (or very long dwell); check
   `dryer_pph(ink) >= press_pph`, else the job runs at dryer speed (§5).
8. **Garment fiber**: poly → low-cure ink + lower dryer temp; discharge → 100% cotton dischargeable dyes only.
9. **Mesh/screen availability**: enough frames of the right mesh and size (screen inventory is a real
   constraint `(derived)`).

### Manual vs auto break-even (quantity)
| Source | Manual | Auto |
|---|---|---|
| Lawson table | 1–72 pcs | 72–10,000+ pcs [8] |
| Ryonet blog | upgrade when regularly >50 pcs [9] | |
| Printable Press | <200 per run fine on manual | >300 per design needs auto [10] |
- Compute instead: `t_manual = setup_m + qty/pph_m` vs `t_auto = setup_a + qty/pph_a`;
  break-even `qty* = (setup_a − setup_m) / (1/pph_m − 1/pph_a)`.
  Example: setup_m 20 min, setup_a 30 min, pph_m 60, pph_a 400 → qty* = 10 / (1/60 − 1/400) h... in min:
  (30−20) / (60/60 − 60/400) = 10 / 0.85 ≈ **12 pcs** of run time; real break-even rises once labor (2 crew
  on auto), dark-garment flash penalty on manual (30 PPH) and auto setup without pins (45 min) are included
  `(derived)`. Lawson's 72 is a reasonable default.
- Color count: color count slows a manual (operator pulls every screen) but not an auto [11] → high-color
  small runs still favor the auto if setup is fast (pin registration).

### Soft ranking factors
- Setup cost amortization (pins/registration system per press).
- Crew available (auto at 2–3 people vs manual at 1).
- Dryer shared with another press running a different ink.
- Same-ink, same-screens jobs back-to-back (save reclaim/setup).

### Sources
1. https://www.mrprint.com/equipment/sportsman-ex-automatic-screen-printing-press
2. https://kolormatrix.com/roq-print-you.html
3. https://impressionsmagazine.com/products/electraprint-junior-series/29620/ ; https://theshirtboard.com/index.php/topic,21679.0.html
4. https://screenprintingmag.com/?p=3394 ; https://kolormatrix.com/collections/pallets (via search summary)
5. https://screenprinting.com/blogs/news/roq-compatible-dual-sleeve-platens-manufactured-by-ryonet
6. https://lawsonsp.com/products/pocket-platen
7. https://www.screenprinting.com/pages/roq-family (ROQ E vs external compressors, via search summary)
8. https://lawsonsp.com/blogs/education-and-training/the-great-debate-manual-vs-automatic-screen-printing (via search summary)
9. https://blog.screenprinting.com/blogs/news/how-do-you-know-its-time-to-upgrade-to-an-automatic-screen-printing-press
10. https://www.printablepress.com/manual-vs-automatic-screen-printing-press/
11. https://www.rushordertees.com/blog/manual-vs-automatic-screen-printing-machine/

---

## 8. Electrical and shop utilities

### Autos (M&R Sportsman EX, official) [1]
| Model | 208/230V 1ph | 208/230V 3ph | 380/415V 3ph | kW | Air @100 psi |
|---|---|---|---|---|---|
| 8/6 (4045, 5050) | 31 A | 20 A | 10 A | 3.3 | 9 CFM (255 l/min) |
| 10/8 | 38 A | 22 A | 11 A | 3.9 | 9 CFM |
| 12/10 | 43 A | 28 A | 14 A | 4.6 | 9 CFM |
| 14/12 | 46 A | 30 A | 17 A | 5.3–6 | 13 CFM |
- Brown ElectraPrint Senior 8/10: all-electric, no compressor, 30 A 220 V 1 ph (forum listing) [2].
- Press electrical excludes flash units; each flash adds its own load (below).
- Single-phase ok for entry autos; 3-phase only cuts amperage. A shop without 3-phase chose a press that
  didn't need it [3].

### Flash units
- Vastex RedFlash/F-1000 18x18: 2,600 W 240 V ~12 A, NEMA 6-15P; high-output 3,500 W 240 V (NEMA 6-20P);
  120 V 1,950 W version [4].
- Riley Hopkins 18x18: 120 V, 2,223–2,300 W, ~19 A → dedicated 20 A circuit [5].
- Amps = W / V (2,600 W @ 240 V ≈ 10.8 A) `(arithmetic)`.

### Dryers
| Dryer | Electrical | Source |
|---|---|---|
| BBC Forced Air 24" (48" chamber) | 240 V 1ph 7,250 W 30 A; or 240 V 3ph 17.5 A | [6] |
| BBC Forced Air 36" | 240 V 1ph 12,000 W 50 A; or 3ph 29 A | [6] |
| Vastex Little Red X2-30 | 5,200 W 240 V 1ph 21.6 A | [7] |
| Vastex Little Red X2D-30 | 6,300 W 240 V 1ph 27 A | [7] |
| Vastex EconoRed II-30 | 7,200 W; sheet lists 240V/58A/3ph FLA (ambiguous) | [8] |
| Vastex EconoRed 3-30 | 10,800 W 240 V 1ph 50 A | [8] |
| Vastex EconoRed 6-30 | 15,600 W 240 V 1ph 68 A / 3ph 41 A | [8] |
| M&R Sprint 2000 (gas) | 300,000 BTU/burner nameplate; ~150–180k BTU/h actual (forum) | [9] |
- Small dryers (Vastex Booster DB18) come in 120 V plug-in [8]. Entry conveyor dryers are almost all 240 V.
- Vendors: amps shown are FLA, not breaker size; electrician sizes circuit [8].

### Compressed air (pneumatic autos)
- M&R Sportsman EX: 9 CFM @ 100 psi (8–12 color), 13 CFM (14/12) [1].
- Forum: 6-color Javelin ~15–20 CFM @ 100 psi; 27 CFM compressor + 120-gal tank ran nearly continuously with
  5+ heads [10]. One-man shop: 7.5 hp Ingersoll, 80-gal tank, chiller [3].
- Lawson: larger Workhorse autos need 10 hp (34.8 CFM @ 175 psi package) [11].
- Single-phase limit: ~7.5 hp (20–30 CFM) largest single-phase compressor [11].
- Rotary screw preferred for continuous duty; reciprocating = intermittent duty only (Anatol) [12].
- Air dryer/chiller recommended; humid air rusts press [11].
- Rule: buy compressor CFM ≥ 1.5–2× press nameplate `(unverified rule of thumb)`.

### Sources
1. https://www.mrprint.com/equipment/sportsman-ex-automatic-screen-printing-press
2. https://theshirtboard.com/index.php/topic,21679.0.html
3. https://theshirtboard.com/index.php/topic,4360.msg48315.html
4. https://www.printing.org/content/2018/08/23/vastex-f-1000-flash-cure-unit-now-33-faster ; https://kolormatrix.com/products/red-flash-cure-240v-various-sizes
5. https://screenprinting.com/products/rileyflash-dryer-18-x-18 ; https://greengalaxy.ca/products/riley-flash-dryer-plus-18-x-18
6. https://assets.stahls.com/stahls/content/pdf/techsheets/Forced-Air-Conveyors-Application-Sheet.pdf
7. https://aaprintsupplyco.com/products/vastex-littlered-series-x2-mid-level-heater-infrared-dryers-7-long ; https://kolormatrix.com/products/little-red-x2d-series-30-x-5-5-dryer
8. https://www.worklinestore.com/storage/allegati_prodotti//prodotto_1321_all_144_er-ii_1019.pdf ; https://kolormatrix.com/econored-3-30-x-8-75-dryer.html ; https://kolormatrix.com/econored-6-30-x-13-5.html
9. https://www.vavato.com/en/l/2016-m-r-sprint-200-textieldrukmachine-%282x%29-A3-34606-3333 ; https://theshirtboard.com/index.php/topic,26720.0.html
10. https://theshirtboard.com/index.php/topic,8441.0.html
11. https://lawsonsp.com/products/10hp-air-compressor-package ; https://design.instrumart.com/blog/applications/1012/how-to-choose-air-compressors-for-screen-printing-equipment
12. https://anatol.com/wp-content/uploads/2020/10/Air-Compressor-Buying-Guide.pdf (404 at fetch time; via search summary)

---

## 9. Glossary and manufacturers

### Glossary
- **AOP** — all-over print; oversize pallets/screens.
- **Blocker / barrier base** — grey or black UB that stops poly dye migration.
- **Catcher / unloader** — person pulling shirts off pallets onto the dryer belt.
- **Chamber (heat chamber)** — heated section of a conveyor dryer; its length sets dwell at a belt speed.
- **CTS** — computer-to-screen imaging (no film); pairs with pin registration.
- **Discharge** — ink that bleaches garment dye (ZFS activator); no UB on dark cotton.
- **Donut probe / temp strips** — tools to read actual ink/garment temp in the dryer.
- **Double hit** — printing the same layer twice (PFP or two screens).
- **Durometer** — squeegee hardness (Shore A).
- **Dwell** — time in the dryer heat chamber (or under a flash).
- **Emulsion / stencil** — photo-sensitive coating exposed to make the image.
- **FLA** — full load amps (not breaker size).
- **Flash / flash cure** — gel a layer between prints.
- **Floodbar / flood stroke** — fills stencil with ink, no pressure.
- **Gel** — partially fused plastisol, dry to touch, can be printed over.
- **Haze / ghost** — residual stain after reclaim; haze remover.
- **Head** — print position (= one "color" of a press).
- **Highlight white** — final white on top of colors, usually higher mesh.
- **HSA** — high solids acrylic (Green Galaxy WB line).
- **Index** — rotation of pallets by one position.
- **Load station** — headless station for loading garments.
- **LPI** — halftone lines per inch.
- **Low-cure / low-bleed** — plastisol that fuses below poly dye migration temp (~260–290°F).
- **Mesh count** — threads per inch (US) or per cm (EU).
- **Micros** — micro-registration knobs.
- **Off-contact** — screen-to-garment gap.
- **Pallet / platen** — board holding the garment (= station).
- **PFP / PFPF** — print-flash-print(-flash).
- **Pin registration** — Tri-Loc/Shurloc-type system aligning screens off-press.
- **Plastisol** — PVC + plasticizer ink; doesn't dry in air, cures by heat (~320°F).
- **Reclaim** — strip ink + emulsion from a screen for reuse.
- **Revolution** — one trip of a pallet around an auto.
- **RFU** — ready for use (no mixing).
- **Sim process** — simulated process; spot-color halftone seps on darks (UB + many colors).
- **Station** — pallet position on the carousel.
- **Tension (N/cm)** — mesh tightness on frame.
- **Thin thread** — 35–45 µm thread mesh; more open area.
- **Underbase (UB)** — white (or grey) first layer on dark garments.
- **Water-based (WB)** — ink that cures by evaporating water + crosslinking; needs forced air.
- **Wet-on-wet** — printing colors without flashing between.
- **ZFS** — zinc formaldehyde sulfoxylate, discharge agent.

### Manufacturers by category (non-exhaustive)
- **Automatic presses**: M&R (Sportsman, Diamondback, Challenger, Gauntlet), ROQ (YOU, Fit, Eco, E), Anatol
  (Volt, Vector), Workhorse/Lawson (Cutlass, Express-EX), Brown (ElectraPrint Jr/Sr), Hirsch/MHM (S-type,
  Matrix), Vastex (V-2000HD), Tuf, Ryonet Riley Hopkins (via ROQ).
- **Manual presses**: M&R (Chameleon, Sidewinder), Anatol (Titan), Riley Hopkins, Vastex (V-1000, V-2000),
  Lawson, Brown (MasterPrinter), Ryonet.
- **Conveyor dryers**: BBC Industries (Big Buddy, Little Buddy, Forced Air, Aeolus), Vastex (Little Red,
  EconoRed), M&R (Sprint, Radicure, Fusion), Anatol, Lawson, Riley Hopkins, ROQ (ROQTunnel).
- **Flash units**: Vastex (RedFlash, F-1000), Riley Hopkins, BBC, M&R (Cayenne, Passport quartz), Anatol,
  Lawson.
- **Plastisol inks**: Wilflex (Avient/PolyOne; Epic), Rutland (Avient), International Coatings, Union Ink,
  FN-INK (Ryonet), Monarch, Triangle, TRQ.
- **Water-based / discharge**: Green Galaxy (Ryonet), Matsui, Permaset, Virus, Rutland/Avient (Oasis), Wilflex
  Aquaflex, Ryonet discharge.
- **Mesh / frames**: Sefar, Saati, Murakami, Newman Roller Frames, Shurloc, Ryonet/BASELAYR.
- **Registration**: Tri-Loc, Shurloc EZ, ROQ pin system.
- **Exposure / CTS**: Vastex (E-series LED), Ryonet (FX LED), M&R (i-Image), Lawson, CTS units.

### Sources
1. Glossary synthesized from sources in §§1–8; manufacturer list from product pages cited above plus
   https://LawsonSP.com/collections/automatic-screen-printing-presses and
   https://imprintnext.com/blog/top-10-conveyor-dryers-for-screen-printing (some model names `(unverified)`).

---

## 10. Open questions for the shop owner

### Already answered by Trevor (onewitharts, 2026-10-24). Use these; do not re-ask.
- Presses: an **M&R Kruzer 6C/4S** manual (6 colours / 4 stations) with **no flash of its own**, and a
  **Brown AP-67J** ("AP67jr") automatic, 6 heads / 7 pallets. The AP-67J's built-in flash is the only flash
  the shop owns. On the auto a flash takes a head: 6 colours only wet-on-wet, 5 with a flash.
- Presses index to the right by default (some newer ones go either way).
- The Brown ElectraPrint manual is the claude.ai skill `trevskills-brown-electraprint`.
- Dryers: manual → BBC forced-air 8 ft ("Black Body"), cures waterbased (1:30–2:00 dwell) and plastisol.
  Auto → BBC Little Buddy, plastisol only for now. BBC Aeolus planned.
- Underbase on the auto = two screens (UB on head 1, flash head 2, cool-down head 3 if available, colours
  after). On the manual = one screen on the same platen (the manual has no flash).
- Manual rate ≈ 100 shirts per 4 hours on a dark-garment print-flash-print job (≈25 PPH); black ink with
  no flash is much faster.
  Auto rate unknown until measured; "500/hr" claims are a label, never a default.
- Manual is right for ≤ ~50 pieces. Shirts are stacked and wait when the dryer falls behind
  (estimate = slower of press and dryer). Front and back are separate runs.
- All rates are user-entered per press and dryer; the app never uses a published PPH in an estimate.

Shop ink practice (Trevor, 2026-10-26):
- Waterbased groups: **HSA** (clear base, e.g. Matsui OW Stretch); **HSA+** (white base, 70%+ white components;
  acts as its own underbase, so print-flash-print straight onto black shirts with no separate underbase screen);
  **LSA** (e.g. Matsui 301 RC Neo); **discharge**.
- Plastisol groups: **Normal** and **Softhand** (additive; feels more like LSA; light garments).
- LSA and discharge avoid formulas with 50%+ white (thicker, less soft and breathable).
- Discharge never needs an underbase. Some shops print clear discharge as an underbase, flash, then LSA on top.
  This shop never flashes discharge (formaldehyde, poor ventilation): never suggest flashing it.
- Ink usage per run depends on mesh, stroke count (flood-print vs flood-print-flood-print uses more ink,
  possibly near double, unmeasured) and above all each screen's open area. Trevor will weigh containers
  before and after runs to measure. No default usage figure exists.
- Trevor keeps jars of every mixed ink. An empty jar of a stock formula saves a new jar (~$1.50) and label.

### Still open

Sources disagree or the answer is shop-specific. Ask; store answers as config, not constants.

**Equipment inventory**
1. Manual max print area and frame size.
2. Does the AP-67J flash sit in a head (assumed yes) or in a flash port between heads?
3. "Black Body 8 ft": BBC Forced Air FA-244 (forced air) or Big Buddy III (infrared)? Belt width and
   heated chamber length of each dryer if the catalog row is wrong.
4. Compressor CFM / hp / tank; does it limit running the auto and a flash together?
5. Platens owned: sleeve, pocket, youth, oversize, hoodie; which press each fits.

**Process choices**
6. Mesh defaults by ink and role (UB, highlight, top colours, WB, discharge). 200 or 230 for UB on the auto?
7. Default dwell and dryer temperature per ink type (plastisol, low-cure, WB, discharge).
8. Poly / blends: grey blocker always? Which low-cure ink? Lower dryer setting?
9. Discharge: pot life used? Test print first?

**Time model (calibrate)**
10. Manual PPH on black ink with no flash, and on multi-colour jobs (only the ≈25 PPH
    dark-garment print-flash-print figure is known).
11. Setup minutes: base + per screen, with and without pin registration; manual vs auto.
12. Teardown and reclaim minutes per screen.
13. Crew per press (solo vs loader + catcher) and how PPH changes with crew.
14. Colour-change time between jobs sharing screens.

**Scheduling rules**
15. Max colours the shop will run on each press; will it program a second revolution rather than pull a
    screen?
16. Mixed ink on one dryer: allowed in one shift, or batch by ink?

**Electrical**
17. Service: single or 3-phase? Panel capacity.

### Sources
- See §§1–8.
