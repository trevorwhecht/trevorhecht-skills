---
name: trevskills-nextjs-ui
description: Use when building any frontend UI component, page, or feature in a Next.js project with shadcn/ui and Tailwind CSS. Covers component selection, modal patterns, styling rules, layout, accessibility, and mobile responsiveness.
---

# Next.js UI Development

## Overview

shadcn-first, modal-first, mobile-first UI development for Next.js + Tailwind + shadcn/ui projects. Use existing primitives before building custom.

## Style Guide

Before writing any UI code, check for `.claude/rules/ui-theme.md` in the project root. If it exists and has content, it is the authoritative style guide — follow its palette, typography, icon set, and chart conventions exactly. Do not invent visual decisions that conflict with it.

If the file exists but is empty, note that `/ui-ux-pro-max` should be run to fill it in before making foundational style decisions.

## Required Sub-Skills

Invoke both before writing any UI code — do not skip:

- **REQUIRED SUB-SKILL:** Invoke `shadcn` — live project context, component rules, CLI workflow
- **REQUIRED SUB-SKILL:** Invoke `nextjs-shadcn` — page structure, client boundaries, Next.js data patterns

## Core Rules

**shadcn-first:** Before building any UI element, check available components via the `shadcn` skill. Never build from scratch what shadcn provides.

**Modal-first:** Prefer overlays over page navigation.

| Situation | Component |
|-----------|-----------|
| New entity creation | `Dialog` |
| Entity detail view | `Dialog` |
| Multi-field edit / side panel | `Sheet` |
| Destructive action (delete, archive) | `AlertDialog` |
| Success / error feedback | `toast` (Sonner) |
| Card list → detail | Card → `Dialog`, not new route |

**Inline editing:** Single-field edits happen inline. Multi-field edits open a `Sheet`.

**Nav pattern:**
- Dashboards → Sidebar nav (desktop) / collapsible or bottom nav (mobile)
- Content / marketing sites → Top nav with hamburger on mobile
- Bottom nav: max 5 items, always include icon + text label
- Back navigation must be predictable — preserve scroll position and state when returning

## Accessibility

These are not nice-to-haves — they are correctness requirements.

**Color contrast:** Text must meet 4.5:1 against its background (3:1 for large text). Never use gray-on-gray. Use CSS variable pairs that are validated together.

**Focus rings:** Never remove the focus ring with `outline-none` unless you replace it with a visible custom style. Keyboard users depend on it.
```tsx
// ✗ — removes all keyboard navigation feedback
className="focus:outline-none"

// ✓ — replaces with visible custom ring
className="focus-visible:ring-2 focus-visible:ring-[var(--color-primary)] focus-visible:outline-none"
```

**Icon-only buttons:** Always add `aria-label`:
```tsx
<Button variant="ghost" size="icon" aria-label="Delete item">
  <Trash2 className="h-4 w-4" />
</Button>
```

**Icons:** Use SVG icons (Lucide, Heroicons) — never emojis as icons. Keep one consistent icon set and stroke width throughout the product.

**Heading hierarchy:** Never skip heading levels (h1 → h3). One `h1` per page.

**Don't rely on color alone** to convey meaning — pair color with an icon or text label (e.g. error state = red + error icon + message, not just red).

## Animation

Keep transitions fast and purposeful. Decorative-only animation is noise.

- **Duration:** 150–300ms for micro-interactions; complex transitions ≤400ms
- **Properties:** Animate `transform` and `opacity` only — never `width`, `height`, `top`, `left` (causes layout reflow)
- **Easing:** `ease-out` for entering elements, `ease-in` for exiting
- **Reduced motion:** Always pair with `motion-reduce:transition-none`
- **Loading states:** Show a layout-matched skeleton (see Skeleton Loaders) when loading exceeds 300ms; spinners are for action buttons only.

```tsx
// ✓ — performant, respects reduced motion
className="transition-opacity duration-200 ease-out motion-reduce:transition-none"

// ✗ — animating layout properties causes reflow
className="transition-all duration-300"  // never "all"
```

## Skeleton Loaders

Show grey placeholder bars that match the real layout whenever the UI waits on data — never a bare spinner for content. Spinners (`Loader2`) are ONLY for action-pending buttons (form submits), never for data loading.

**Skeletons are ONLY for dynamic (server/async) data.** Static, hardcoded content — nav labels, section headings, sidebars, column titles, any text the component renders without waiting on a fetch — must render IMMEDIATELY and must NEVER be replaced by a skeleton bar. Skeleton only the parts that are actually loading. A skeleton over static content is a bug: it makes instant content look slow.

**Persistent chrome belongs in `layout.tsx`, not the skeleton.** If a shell element is static and shared across a route's states (a dashboard sidebar, a section header), render it in the route's `layout.tsx` so it paints instantly and stays mounted. Then `loading.tsx` covers ONLY the dynamic content area — the chrome is never skeletoned at all. Example: `dashboard/layout.tsx` renders the real sidebar + `{children}`; `dashboard/loading.tsx` renders only the kanban-content skeleton.

**Decouple independent data sources.** When one region depends on data A and another on data B, gate each on its own loading flag. Render A's real content the moment A resolves, skeletoning only B — don't hold the whole view behind `aLoading || bLoading`. (e.g. kanban column *titles* come from `orderStates`; *cards* come from `orders` — show real titles as soon as states load, skeleton only the cards.)

**Movement is required — skeletons must shimmer.** A static grey block doesn't read as "loading." The `Skeleton` primitive animates a light gradient sweep (a `::before` `bg-linear-to-r` sheen translating across the bar via the `shimmer` keyframe in `globals.css`), paired with `motion-reduce:before:animate-none`. Never ship a skeleton that only changes opacity or sits still.

**Primitive:** `src/components/ui/skeleton.tsx` — fill is `bg-(--color-border)` (never `bg-muted`, which resolves to a dark text token) plus the shimmer sweep described above.

**Generic composites:** `src/components/shared/skeletons/` — `TableSkeleton`, `CardGridSkeleton`, `FormSkeleton`, `StatTilesSkeleton`. Reuse these before writing bespoke bars.

**Colocated page skeletons:** every data-driven page has a `{Container}-Skeleton.tsx` in the same folder as its container, mirroring that page's real layout (compose from the shared composites where possible). "Mirror" means the same structure — same columns, headers, card shapes, proportions — not a few loose bars.

**Route-level loading:** every dynamic route gets a `loading.tsx` that renders its colocated skeleton, so navigation paints instantly while the server streams:
```tsx
import DashboardSkeleton from "./Dashboard-Skeleton"
export default function Loading() { return <DashboardSkeleton /> }
```
For a client page behind `<Suspense>`, pass the skeleton as the `fallback` instead of text.

**HARD RULE — keep skeletons in sync:** any change to a component's rendered layout MUST update its colocated skeleton in the same change. The skeleton is in the same folder for exactly this reason. A skeleton that no longer matches the UI is a bug.

## Forms

**Error placement:** Always below the related field, never only at the top.

**Validation timing:** Validate on blur — not on every keystroke. Show the error after the user finishes, not while typing.

**Mobile keyboard type:** Use the right `inputMode` or `type` so mobile shows the correct keyboard:
```tsx
<Input type="email" inputMode="email" />        // email keyboard
<Input type="tel" inputMode="tel" />             // phone keypad
<Input type="number" inputMode="numeric" />      // number pad
```

**Autofill:** Use `autoComplete` so the browser/OS can fill in known values:
```tsx
<Input autoComplete="email" />
<Input autoComplete="current-password" />
<Input autoComplete="given-name" />
```

**Submit state — Enter key + spinner (required on every form):**

Every form must use `<form onSubmit={...}>` with a `type="submit"` button — never `onClick`-only submission. This gives Enter/Return key support for free. Every submit button must show a `Loader2` spinner from Lucide while pending. Use `useTransition`, not a boolean state:

```tsx
import { useTransition } from "react"
import { Loader2 } from "lucide-react"

const [isPending, startTransition] = useTransition()

function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
  e.preventDefault()
  startTransition(async () => { /* async work */ })
}

<form onSubmit={handleSubmit}>
  <Input name="value" />
  <Button type="submit" disabled={isPending} className="gap-2">
    {isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
    {isPending ? "Saving…" : "Save"}
  </Button>
</form>
```

**Confirm modals — Enter key support:** Add `autoFocus` to the primary action button in every `AlertDialog` or confirmation `Dialog` so Enter triggers it:

```tsx
<AlertDialogAction autoFocus onClick={handleConfirm}>Delete</AlertDialogAction>
```

**Destructive actions:** Use semantic danger color (red) and visually separate from the primary CTA. Always confirm with `AlertDialog` before executing.

## Mobile UI

**Every component must look and function equally well on mobile and desktop. Mobile is not optional — design for the smallest screen first.**

### Touch Targets
All interactive elements must be tappable without precision:
```tsx
// Min 44px — shadcn Button sizes meet this; never shrink them below min-h-11
<button className="min-h-11 px-4">Action</button>
```

### Keyboard Behavior
The virtual keyboard covers the bottom ~40% of the screen. Inputs focused while hidden behind it must scroll into view automatically.

```tsx
// ✗ — overflow:hidden blocks the browser from scrolling inputs above the keyboard
<div className="h-screen overflow-hidden">
  <form>...</form>
</div>

// ✓ — scrollable ancestor lets the browser push content above the keyboard
<div className="h-dvh overflow-y-auto">
  <form>...</form>
</div>
```

When auto-scroll isn't enough (inputs inside fixed-position containers, complex layouts), scroll the focused input into view manually after the keyboard finishes animating:
```tsx
const handleFocus = (e: React.FocusEvent<HTMLInputElement>) => {
  setTimeout(() => {
    e.target.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }, 300) // wait for keyboard open animation
}
<Input onFocus={handleFocus} className="text-base" />
```

**Rules:**
- Never use `overflow: hidden` on any ancestor of a form — the browser cannot scroll inputs into view
- Use `h-dvh` not `h-screen` / `h-[100vh]` — dvh tracks the actual visible area as the keyboard opens
- Input must sit visually above the keyboard when focused, not underneath it

### Tables

**Always wrap `<Table>` in `<div className="w-full overflow-x-auto">`, and always put `w-full` on
the table itself.** That part is unconditional — it is what makes a table fill the area you bound
it to instead of shrink-wrapping to its content and leaving dead space beside it.

What *is* conditional is whether that wrapper ever actually scrolls, and that is decided by the
table's `min-width`:

| Columns | What happens |
|---|---|
| **Few** — total minimum fits the container | `w-full` spans the full width, columns share the slack via `fr`. `overflow-x-auto` is present but shows no scrollbar, because nothing overflows. |
| **Maxed** — total minimum exceeds the container | `min-width` holds every column at a legible size and the wrapper scrolls. |

So the wrapper is free: `overflow-x-auto` costs nothing when the content fits. Never omit it to
"prevent" scrolling — that clips content instead of revealing it. To stop a table scrolling, lower
its minimum (the ladder below), never remove its scroll container.

```tsx
// ✓ — the one correct shape, both cases
<div className="w-full overflow-x-auto">
  <table className="w-full min-w-[840px]">   {/* = sum of the column minimums */}
```

#### The ladder — when the minimum exceeds the container

Work down this list before accepting a scroll. Stop at the first step that brings the total under
the container width.

1. **Strip horizontal padding and margins.** Side padding goes first, not last. Kill the card's
   `px-*`, the wrapper's side padding, and drop cell padding to the gutter minimum (`px-2`, or
   `px-1` on mobile). A five-column table that "needs" scrolling usually just has 16px of dead
   space on both sides of every cell.
2. **Shrink the type one step** at the mobile breakpoint (`text-sm` → `text-xs` → `text-[11px]`).
3. **Accept the scroll.** Some tables genuinely cannot fit a phone, and a ten-column table
   scrolling sideways is correct — far better than ten columns wrapped into vertical mush.

**Never hide, drop or move a column, value or button into an expanded row to stop a table
scrolling.** Every column stays visible at every width. A table that does not fit scrolls sideways
inside its own `overflow-x-auto` wrapper.

```tsx
// ✓ — all columns stay; the wrapper scrolls
<div className="w-full overflow-x-auto"><table className="w-full" style={{ minWidth: tableMinWidth(COLUMNS) }}>

// ✗ — columns hidden on phones, their values pushed into an expanded row
<th className="hidden lg:table-cell">COST</th>
```

#### Phones and iPads: columns hug their content

Below 1024px, columns sit as close together as they can without overlapping or clipping. Size each
track to its content using the minimums table below, with a 4px gutter, and no `fr` slack between
number columns (give any leftover space to the name column, or let it scroll). At 1024px and up the
current `fr` fill behaviour is unchanged.

```tsx
// ✓ — below 1024px: tracks sized to content, 4px gutter
<div className="grid gap-1 grid-cols-[32px_48px_88px_88px_minmax(120px,1fr)] lg:gap-3 lg:grid-cols-[32px_1fr_1fr_1fr_2fr]">

// ✗ — number columns spread by fr on a phone, leaving gaps between figures
<div className="grid grid-cols-[32px_1fr_1fr_1fr_2fr]">
```

#### Long text in a narrow cell: wrap, then shrink, then ellipsis

Long text goes through three steps in order: wrap to 2 lines; if it still does not fit, shrink one
type step; if it still does not fit, truncate with an ellipsis and put the full value in `title`.

```tsx
// ✓ — 2 lines, then ellipsis, full value on hover
<div className="line-clamp-2 text-xs" title={name}>{name}</div>

// ✗ — cut to one line with no way to read the rest
<div className="truncate">{name}</div>
```

#### When does it "not fit"? — concrete minimums

Add these up. That sum is the table's `min-width`. If it exceeds the narrowest container the table
lives in (assume **360px** for phone), the table scrolls there; otherwise it never will.

| Column kind | Min width | Notes |
|---|---|---|
| Icon / caret / toggle | `32px` | Caret, expand, drag handle |
| Short number (qty) | `48px` | Up to 4 digits |
| Money | `88px` | Fits `$1,234.56`; `110px` if it can show a range like `$5.25 - $6.50` |
| Short text (color, size, status) | `72px` | |
| Name / style / description | `120px` | The column that should absorb leftover `fr` space |
| Gutter between columns | `12px` desktop, `4px` mobile | `gap-3` / `gap-1` — see "Mobile: tables go edge to edge" |

**Derive the minimum, don't guess it.** Keep the per-column minimums in the same shared column list
that drives the headers, and sum them in a helper. A hand-typed `min-w-[768px]` goes stale the
moment a column is added, and then either squeezes or scrolls for no reason anyone can trace.

For a CSS-grid table, express each track as `minmax(min, grow)` so a column can absorb slack but
never collapse below legibility. One wrapper holding both a mobile and a desktop row must be sized
to whichever needs more — otherwise the wider one squeezes right at the breakpoint.

```tsx
// ✓ — minimum derived from the columns themselves
<div className="w-full overflow-x-auto">
  <div className="w-full" style={{ minWidth: tableMinWidth(visibleColumns) }}>
```

```tsx
// ✗ — hand-typed minimum, stale the next time a column is added
<div className="overflow-x-auto"><table className="min-w-[768px]">

// ✗ — no wrapper, so a wide table overflows the page instead of scrolling in place,
//      and a narrow one shrink-wraps instead of filling its container
<div><table>
```

#### Alignment — left, always

**Headers, their body cells, and the totals row are ALL left-aligned.** Every column reads as one
straight vertical edge from heading to total. Right-aligned numbers under a left-aligned heading is
the most common cause of a table that "looks off" with no obvious reason why.

- Define alignment **once per column** in a shared column list; the header cell, body cell and
  totals cell all read it from there. Never hand-write `text-right` on a cell — that is exactly how
  a header and its column drift apart.
- **No per-cell nudges.** `pl-24`, `-ml-6`, `pl-16` and friends are banned. If a heading does not
  sit over its data, the grid tracks are wrong — fix the track, not the padding. An element that
  needs its own position (an expand caret) gets **its own column**; it does not squat in its
  neighbour's.

```tsx
// ✓ — one definition drives header, cell and total
const COLUMNS = [{ key: 'amount', label: 'AMOUNT', width: '1fr' }]
<div className="text-left">{col.label}</div>

// ✗ — header nudged by hand to sit over a cell it does not share a track with
<div className="pl-24">DESIGN</div>
```

#### Currency: the `$` lines up with the heading

A left-aligned money cell must start its `$` at exactly the same x as the first letter of its
header. That is free when the cell and header share a track, carry the same horizontal padding, and
neither is nudged — so the thing to avoid is padding that differs between the two.

- Same `px-*` on the header cell and the body cell. Set it once on the row, not per cell.
- `tabular-nums` on every money and quantity column, so digits occupy equal width and the figures
  form a clean block down the column.
- Keep the `$` **inside the same text node** as the number (`$12.50`), never as a separately
  positioned prefix element — a floated or absolutely positioned `$` cannot stay aligned.
- A range (`$5.25 - $6.50 & up`) starts at that same left edge; give the column the 110px minimum
  so it does not wrap mid-range.

```tsx
// ✓ — $ is the first glyph of a left-aligned cell on a shared track
<div className="text-left tabular-nums">${amount.toFixed(2)}</div>

// ✗ — right-aligned, so the $ sits at a different x on every row
<div className="text-right">${amount.toFixed(2)}</div>
```

**Editable money cell.** An `<input>` in a money cell keeps the `$` aligned with the header's first
letter, like a plain money cell, and is at least `88px` wide so `$1,234.56` fits.

```tsx
// ✓ — $ stays the first glyph on the shared track; input wide enough for $1,234.56
<input className="w-full min-w-[88px] text-left tabular-nums" defaultValue={`$${amount.toFixed(2)}`} />

// ✗ — narrow input clips the figure
<input className="w-12" />
```

#### In-cell buttons need their own gutter

A cell with an info/help/action button must not let that button crowd the next column.

- `inline-flex items-center gap-1.5` between the value and the button.
- **At least `pr-3` (12px) after the button**, on top of the row gutter, so the icon never visually
  belongs to the column on its right.
- `shrink-0` on the icon so a long value never squeezes it.
- The button keeps its 44px touch target on mobile through padding, not by growing the icon.

```tsx
// ✓
<div className="flex items-center gap-1.5 pr-3 text-left tabular-nums">
  <span>${price.toFixed(2)}</span>
  <button className="shrink-0 p-1 rounded hover:bg-muted" aria-label="Print details">
    <Info className="w-3.5 h-3.5" />
  </button>
</div>
```

#### Mobile: tables go edge to edge

A table is the one thing allowed to break the "content never touches the screen edge" rule. On a
phone, side padding around a table is pure cost — every pixel of inset is a pixel of horizontal
scrolling the user has to do to read the same data.

- **The container drops its side padding at mobile, and the table fills it.** `px-0 sm:px-6` on the
  modal body / page container; the table needs no negative margins at all. Achieve full-bleed by
  *removing* padding from the parent, never by `-mx-*` on the child — a negative margin has to be
  undone at every breakpoint and silently clips when a parent gains `overflow-hidden`.
- **Everything that is not a table opts back in** with its own `mx-3 sm:mx-0`. Headings, button
  rows, totals cards, inputs — if it is not the table, it keeps itself off the edge.
- **The card around a full-bleed table loses its side border and radius on mobile:**
  `border-y sm:border-x sm:rounded-lg`. Keeping a rounded border at the screen edge is what makes
  full-bleed look like a mistake rather than a decision.
- **Tighten the gutter on mobile** — 4px, not 8px. Column minimums are what keep columns apart;
  the gap is just breathing room, and at ten columns an extra 4px each is half a screen of scroll.

```tsx
// ✓ — parent drops padding, table fills, card squares off at the edges
<ModalBody className="px-0 sm:px-6">
  <div className="border-y sm:border-x sm:rounded-lg border-(--color-border)">
    <div className="w-full overflow-x-auto"> …table… </div>
  </div>
  <div className="mx-3 sm:mx-0"> …everything that is not a table… </div>
</ModalBody>

// ✗ — negative margin fighting the parent's padding at every breakpoint
<div className="overflow-x-auto -mx-4 px-4 md:mx-0 md:px-0">
```

#### Other rules

- `whitespace-nowrap` on names, dates, IDs, status badges and numbers. Never truncate or wrap table
  data to dodge a scroll, except long text in a narrow cell as the long-text rule allows — once you
  are at step 3 of the ladder, scrolling is the correct answer.
- Give the scroll container standard affordance: `overflow-x-auto` with `scrollbarWidth: 'thin'`
  and a muted thumb, so the scrollbar reads as part of the design rather than an accident.
- A totals row carries one empty cell per column it does not fill, so it stays on the same tracks as
  the rows above. Never span or pad it into position.

#### Inline-edit number cell (edit-in-place in a table)

When a numeric table cell (qty, price, cost) should be editable **in place** — no modal, no expanding row — use a compact, borderless input that reads like the static cell until focused. Extract it as ONE reusable component and use it for every editable numeric column (DRY — never copy the styling per cell).

The classNames are the important part (works with a shadcn or NextUI `Input`):
- **Aligns with static cells:** `text-left` + `tabular-nums`, matching the left-aligned column it sits in (see Alignment above); wrap in the same `flex pr-2` the static number uses so the digits line up exactly.
- **Invisible at rest, obvious when active:** transparent, no border; on focus show a subtle highlight + ring only — e.g. `group-data-[focus=true]:bg-white/10 group-data-[focus=true]:ring-1 group-data-[focus=true]:ring-white/30 rounded-sm`.
- **Sized to the number, not the cell:** a fixed narrow width (`w-12` desktop / `w-10` mobile) so the highlight hugs the value.
- **Hide native spinners:** `[appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none`.
- **Mobile fast-entry:** empty the field on focus **only on mobile** (`window.innerWidth < 768`) so you can type without backspacing; on blur, if nothing was typed, keep the previous value (don't zero it).
- **Keep the parent's logic:** the component is a pure styling/behavior wrapper — the parent still owns the value + `onChange` (sanitize + live recalc) + `onBlur` (commit), so per-column validation is untouched.
- Always pass an `aria-label`; use `inputMode="numeric"` (integers) or `"decimal"` (money) and a `$` `startContent` for money columns.

Reference implementation in this stack: `src/components/InlineNumberInput.tsx` (NextUI) — props `value / onValueChange / onCommit / onMobileFocusClear / prefix / type / widthClass / textSizeClass`.

### Scroll Behavior
Scrolling must be on by default. Only disable it for specific interaction contexts where a different touch gesture is intentional:

```tsx
// Standard page — always scrollable, uses accurate mobile height
<div className="min-h-dvh overflow-y-auto">

// Photo / image viewer — allow pinch-zoom, prevent accidental page scroll
<div className="overflow-hidden" style={{ touchAction: 'pinch-zoom' }}>
  <Image fill src={src} alt={alt} className="object-contain" />
</div>

// Map, canvas, custom gesture area — full gesture control
<div style={{ touchAction: 'none' }}>

// All buttons and tappable elements — removes 300ms double-tap delay without blocking scroll
<button className="touch-manipulation">
```

| `touch-action` | When to use |
|---|---|
| *(default)* | Normal scrollable content — never override unless needed |
| `manipulation` | All buttons/links — snappier taps, scroll still works |
| `pinch-zoom` | Image/photo viewers — allows zoom, prevents scroll |
| `none` | Custom gesture areas (maps, canvas, drag handles) |

### Modal Placement — centred when short, pinned under the nav when tall

**Scope this to the breakpoint that actually has the problem.** Desktop usually has room to centre
a modal and already looks right; mobile is where it goes wrong. Changing both when only one was
asked for is a regression, however good the new behaviour is. Confirm which breakpoint before
touching placement.

On mobile, two rules, and one CSS trick satisfies both without a breakpoint or a measurement:

- **Short modal → vertically centred** in the space below the navbar.
- **Tall modal → flush under the navbar**, filling down to a small bottom gap.

```tsx
// ✓ — mobile gets the new behaviour; every value is sm:-reverted to the component's own default
<Modal
  placement="top-center"                 // => items-start sm:items-center
  scrollBehavior="inside"
  classNames={{
    wrapper: "pt-[var(--app-navbar-height)] pb-2 sm:pt-0 sm:pb-0",
    base: "my-auto max-h-full sm:my-16 sm:max-h-[calc(100%-8rem)]",
  }}
/>
```

`placement="top"` would top-align **desktop too**, stranding a short modal high on the screen.
`top-center` is the one that means "top on mobile, centred on desktop".

**Why `my-auto` and not `items-center`:** per the flexbox spec, auto cross-axis margins absorb free
space *before* `align-items` is consulted. Free space → the modal centres. No free space → the auto
margins resolve to `0` and `items-start` takes over, putting it hard against the top. Centring with
`items-center` cannot do this: an over-tall item overflows equally in both directions and **its top
scrolls out of reach**.

**Component defaults that fight this (HeroUI, verified in `@heroui/theme`):**

| Default | What it does | Fix |
|---|---|---|
| `placement="auto"` | `items-end sm:items-center` — **bottom-pins every modal on mobile** | `placement="top-center"` (NOT `"top"`, which top-aligns desktop too) |
| base `my-1 sm:my-16` | on mobile, no relationship to where the nav ends | `my-auto sm:my-16` — override mobile, hand `sm:` straight back |
| `scrollBehavior="inside"` → `max-h-[calc(100%-8rem)]` | on mobile the modal can never fill its space; it stays short and scrolls internally while screen sits empty | `max-h-full sm:max-h-[calc(100%-8rem)]` — same deal |

Note every Fix restates the component's own `sm:` value rather than dropping it. Overriding a
default for mobile silently changes desktop too unless you put it back explicitly, and "desktop was
already fine" is the usual case.

**Never bottom-pin a modal on mobile.** It reads as a dismissed sheet and puts the title furthest
from the thumb. Centred or top-pinned only.

The nav offset reads a token (`--app-navbar-height` on `:root`), never a literal — otherwise the
modal drifts the moment the nav height changes. Keep the token and the `<Navbar height>` in sync.

Put all of this in ONE shared module and import it into every modal (`src/lib/modalLayout.ts`) —
copying the class strings per modal is how half of them end up bottom-pinned again.

**⚠️ A shared class-string constant only works if Tailwind scans the file it lives in.** Tailwind
generates CSS by scanning `content` paths for literal class names. A constant in a folder that is
not listed — `src/lib/`, `src/config/`, `src/constants/` — produces **no CSS rule at all**, with no
error, no warning, and a build that passes. The class is in the DOM and does nothing.

```js
// tailwind.config.ts — add every folder that can hold a class-name string
content: [
  "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
  "./src/lib/**/*.{js,ts,jsx,tsx}",   // ← shared class-name constants
]
```

This failure is easy to misread, because props still work while strings do not: a component's own
`placement="top"` resolves through its theme (which *is* scanned) and applies, while the
`pt-[var(--navbar-height)]` sitting next to it in a constant silently does nothing. The result
looks like a half-applied design rather than a build problem.

**Verify, don't assume:** build the stylesheet and grep for the class. Tailwind escapes the name,
so search for a fragment rather than the literal:

```bash
npx tailwindcss -i src/app/globals.css -o /tmp/out.css
grep -o "pt-[^{ ]*navbar-height[^{ ]*" /tmp/out.css   # => pt-\[var\(--navbar-height\)\]
```

### Modals and Safe Areas
The browser URL bar (Chrome Android) and iOS home indicator eat into the bottom of the viewport. Action buttons at the bottom of a modal will be hidden if you don't add safe-area padding.

```tsx
// ✗ — Save button may be hidden under home indicator
<DialogFooter className="p-4">
  <Button>Cancel</Button>
  <Button>Save</Button>
</DialogFooter>

// ✓ — safe area padding guarantees buttons are always visible
<DialogFooter className="p-4 pb-[max(1rem,env(safe-area-inset-bottom))]">
  <Button>Cancel</Button>
  <Button>Save</Button>
</DialogFooter>

// Full-screen Sheet or Dialog: use h-dvh, not h-screen
<SheetContent className="h-dvh overflow-y-auto">
```

`env(safe-area-inset-bottom)` only has a non-zero value when `viewport-fit=cover` is set. Add this to `app/layout.tsx`:
```tsx
export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  viewportFit: 'cover',  // required — without this, safe-area-inset-bottom is always 0
}
```

**Rules:**
- Every `DialogFooter` / `SheetFooter` with action buttons needs `pb-[max(1rem,env(safe-area-inset-bottom))]`
- Use `h-dvh` everywhere you would use `h-screen` or `h-[100vh]`
- `viewport-fit: cover` must be set globally — it's a prerequisite for all safe area insets

### Input Font Size
Safari auto-zooms the page when any focused input has `font-size < 16px`. Always use `text-base` or larger:
```tsx
<Input className="text-base" />
```

### Hover-Only Interactions
Anything that only appears on hover is invisible on touch devices:
```tsx
// ✗ — invisible on mobile
<div className="group">
  <Button className="opacity-0 group-hover:opacity-100">Delete</Button>
</div>

// ✓ — always visible on mobile, fades in on desktop hover
<div className="group">
  <Button className="sm:opacity-0 sm:group-hover:opacity-100">Delete</Button>
</div>
```

### Edge Spacing
Content must never touch screen edges:
```tsx
<div className="px-4 md:px-6 lg:px-8">
```

**One exception: tables on mobile.** A data table goes edge to edge on a phone — side padding
there is pixels of horizontal scrolling bought for nothing. Everything beside the table still
keeps its gutter. See "Mobile: tables go edge to edge" under Tables.

## No Scrollbars Until the Full Page Is Utilized

**Rule:** Never add `overflow-y-auto`, `overflow-x-auto`, or `overflow-scroll` to a container unless the viewport has genuinely been filled and there is no room left. Let content grow and let the page scroll instead.

**This is about VERTICAL scroll regions.** It does not apply to the horizontal scroll container a
data table always carries (see Tables): that wrapper is unconditional and costs nothing, because
`overflow-x-auto` shows no scrollbar until the content actually exceeds the table's `min-width`.
Removing it does not prevent scrolling — it clips content instead.

```tsx
// ✗ — forces an inner scroll region when page space is still available
<div className="overflow-y-auto max-h-64">...</div>

// ✓ — constrain scroll only on desktop where columns compete for height
<div className="overflow-y-auto md:max-h-[calc(100dvh-12rem)]">...</div>
```

Mobile layouts almost never need inner scroll containers — a single-column view should just grow and let the page scroll. Only add `overflow-y-auto` with a `max-h` when multiple competing containers genuinely fill the viewport (e.g. a desktop kanban with side-by-side columns).

---

## Never Transparent Backgrounds

Every card, dialog, sheet, dropdown, popover, tooltip, and floating element **must have an explicit background**. Never rely on the browser's transparent default.

| Surface | Class |
|---|---|
| Dialog / modal / page content | `bg-(--color-background)` |
| Card / sidebar / dropdown | `bg-(--color-surface)` |

```tsx
// ✗ missing background — transparent over any parent
<div className="rounded-lg border border-(--color-border) p-4">

// ✓ always explicit
<div className="rounded-lg border border-(--color-border) bg-(--color-background) p-4">
```

When copying any shadcn component, always check for a missing `bg-` and add one before committing.

## Shareable Links — Descriptive URLs

Shareable links must be human-readable in both the URL and the OG metadata.

**URL:** Always append `?name=` with the entity's name so the URL is self-explanatory:
```tsx
// ✗
`${base}/orders/${order.token}`

// ✓
const label = order.nickname ?? `Order #${order.id}`
`${base}/orders/${order.token}?name=${encodeURIComponent(label)}`
```

**OG title:** `Entity #id — Name | App Name` — never just an ID or bare name.

**Checklist:** URL has `?name=`, `og:title` is fully descriptive, `og:image` uses `/api/og/` route with `?v=updatedAt` cache buster, `twitter:card: summary_large_image`. Full patterns in `.claude/rules/ui-theme.md`.

## Tailwind 4 + shadcn Compatibility

**Problem:** shadcn installs CSS variables like `--popover`, `--muted`, `--accent` in `:root`. Tailwind 4 needs `--color-{name}` in `@theme inline` to generate `bg-{name}` / `text-{name}` utilities. These naming conventions don't match — shadcn utility classes are silently transparent/missing.

**Rule:** Never use these class names in Tailwind 4 shadcn projects — they produce invisible/transparent output:

| ✗ Broken | ✓ Use Instead |
|---|---|
| `bg-primary` | `bg-(--color-primary)` |
| `text-primary-foreground` | `text-(--color-primary-foreground)` |
| `bg-secondary` | `bg-(--color-surface)` |
| `text-secondary-foreground` | `text-(--color-foreground)` |
| `bg-popover` | `bg-(--color-background)` |
| `text-popover-foreground` | `text-(--color-foreground)` |
| `bg-muted` | `bg-(--color-surface)` |
| `text-muted-foreground` | `text-(--color-muted)` |
| `bg-accent` | `bg-(--color-surface)` |
| `text-accent-foreground` | `text-(--color-foreground)` |
| `focus:bg-accent` | `focus:bg-(--color-surface)` |
| `border-input` | `border-(--color-border)` |
| `border-ring` / `ring-ring/50` | `border-(--color-primary)` / `ring-(--color-primary)/50` |
| `ring-foreground/10` | `ring-(--color-border)` |
| `bg-border` | `bg-(--color-border)` |
| `text-destructive` | `text-(--color-danger)` |
| `bg-destructive/10` | `bg-(--color-danger)/10` |

Remove all `dark:` variant classes — theming is handled via CSS variables, not Tailwind's dark mode system.

When copying shadcn component code from docs/AI/anywhere else, always audit and replace these class names before committing. This applies to `src/components/ui/`, modals, dropdowns, and any popup/overlay.

## Styling

**CSS variables only for colors** — never hardcode Tailwind palette classes. Use Tailwind 4 CSS variable shorthand syntax:
```tsx
// ✓ — Tailwind 4 CSS variable shorthand
className="bg-(--color-primary) text-(--color-foreground)"
// ✓ — also valid explicit syntax
className="bg-[var(--color-primary)] text-[var(--color-foreground)]"
// ✗ — never hardcode palette values
className="bg-blue-600 text-gray-900"
```

**Responsive layout — mobile-first:**
```tsx
// Flex direction switch
<div className="flex flex-col md:flex-row gap-4">

// Responsive grid with explicit breakpoints
<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">

// Auto-fit grid (no breakpoints needed, fits by content width)
<div className="grid grid-cols-[repeat(auto-fit,minmax(250px,1fr))] gap-4">
```

**Container queries** — use when a component should respond to its container width, not the viewport:
```tsx
<div className="@container">
  <div className="text-base @lg:text-xl @2xl:text-2xl">
    Scales with container, not screen
  </div>
</div>
```

**Group hover** — for child effects triggered by parent hover:
```tsx
<div className="group cursor-pointer">
  <img className="group-hover:opacity-75 transition motion-reduce:transition-none" />
  <p className="group-hover:text-[var(--color-primary)] transition motion-reduce:transition-none">
```

**Motion accessibility** — always pair transitions with reduced-motion guard:
```tsx
className="transition duration-200 motion-reduce:transition-none"
```

**Z-index scale** — never use arbitrary z-index values. Use a defined scale:
```tsx
// Define in globals.css or as Tailwind config values
// z-0   — base content
// z-10  — sticky elements, floating labels
// z-20  — dropdowns, popovers
// z-40  — modals, dialogs
// z-100 — toasts, notifications
// z-[1000] — critical overlays (video player, lightbox)
```

**List virtualization** — lists with 50+ items must be virtualized. Rendering hundreds of DOM nodes kills scroll performance. Use `@tanstack/react-virtual` or similar.

**Images** — always `<Image>` from `next/image`, never raw `<img>`:
```tsx
import Image from 'next/image'
<Image src={src} alt={alt} className="aspect-video w-full object-cover" />
```

## Shareable Links — Open Graph Metadata

Any route with a shareable link **must** implement OG metadata so social/messaging app previews show a title and image. Two files required per shareable entity:

**`app/(pages)/[entity]/[id]/layout.tsx`** — exports `generateMetadata()` that fetches the entity and returns `openGraph` + `twitter` metadata. Use a layout (not page) so metadata is server-rendered even when the page is a client component.

**`app/api/og/[entity]/[id]/route.tsx`** — returns a 1200×630 `ImageResponse` using `next/og`. Always set `Cache-Control: no-store, max-age=0` to prevent stale share previews after edits.

**Required on both files:** `export const dynamic = "force-dynamic"`

**Cache buster pattern** — append to the OG image URL in `generateMetadata`:
```ts
const imageUrl = `${siteUrl}/api/og/orders/${order.id}?v=${order.updatedAt.getTime()}`
```

**Metadata shape:**
```ts
return {
  title,
  openGraph: {
    title, description, url: canonicalUrl,
    images: [{ url: imageUrl, width: 1200, height: 630, alt: title }],
  },
  twitter: { card: "summary_large_image", title, images: [imageUrl] },
}
```

Always provide a fallback image (static file in `/public`) for when the entity is not found. Full code patterns are in `.claude/rules/ui-theme.md` under "Shareable Links".

## Component Placement

Before creating any new component:
1. Check `src/components/shared/` for an existing match
2. Ask before creating something new if a near-match exists
3. New shared components go in the correct subfolder: `tables/`, `modals/`, `forms/`, `layout/`
4. Drop the container prefix when promoting a feature component to shared

## Quick Reference

| Need | Solution |
|------|----------|
| Modal / overlay | shadcn `Dialog` |
| Side panel | shadcn `Sheet` |
| Confirm destructive | shadcn `AlertDialog` |
| Notifications | shadcn `Sonner` toast |
| Data table | `src/components/shared/tables/` + always a `w-full overflow-x-auto` wrapper + `w-full` on the table; `min-width` derived from the column minimums, so it scrolls only when maxed out |
| Large list (50+ items) | Virtualize with `@tanstack/react-virtual` |
| Form inputs | shadcn `Form` + `Input` / `Select` / etc. — always `text-base` |
| Edit number in a table cell | Reusable borderless inline input — see "Inline-edit number cell" under Tables (`InlineNumberInput.tsx`) |
| Icon-only button | Add `aria-label` always |
| Icons | Lucide / Heroicons SVG — never emoji |
| Image | Next.js `<Image>` |
| Spacing tokens | Tailwind scale (4, 8, 12, 16…) |
| Color | CSS variable via `[var(--name)]` |
| Touch-safe button | `min-h-11` + `touch-manipulation` |
| Screen edge spacing | `px-4 md:px-6 lg:px-8` |
| Full-height container | `h-dvh` / `min-h-dvh` — never `h-screen` on mobile |
| Modal footer buttons | `pb-[max(1rem,env(safe-area-inset-bottom))]` |
| Image viewer | `overflow-hidden` + `touchAction: 'pinch-zoom'` |
| Keyboard-safe form | Scrollable ancestor (`overflow-y-auto`) + `h-dvh` |
| Mobile keyboard type | `inputMode="email"` / `"numeric"` / `"tel"` |
| Focus ring | `focus-visible:ring-2` — never bare `focus:outline-none` |
