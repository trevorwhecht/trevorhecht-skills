# Tables

### Tables

**Always wrap `<Table>` in `<div className="w-full overflow-x-auto">`, and always put `w-full` on
the table itself.** That is unconditional: it makes the table fill its area instead of
shrink-wrapping. Whether the wrapper ever scrolls is decided by the table's `min-width` — when the
column minimums fit, columns share the slack via `fr` and no scrollbar shows; when they do not, the
wrapper scrolls. Never omit the wrapper to "prevent" scrolling — that clips content. To stop a
table scrolling, lower its minimum (the ladder below).

```tsx
// ✓ — the one correct shape, both cases
<div className="w-full overflow-x-auto">
  <table className="w-full min-w-[840px]">   {/* = sum of the column minimums */}

// ✗ — no wrapper: a wide table overflows the page, a narrow one shrink-wraps
<div><table>
```

#### The ladder — when the minimum exceeds the container

Work down this list before accepting a scroll. Stop at the first step that brings the total under
the container width.

1. **Strip horizontal padding and margins.** Side padding goes first, not last. Kill the card's
   `px-*`, the wrapper's side padding, and drop cell padding to the gutter minimum (`px-2`, or
   `px-1` on mobile).
2. **Shrink the type one step** at the mobile breakpoint (`text-sm` → `text-xs` → `text-[11px]`).
3. **Accept the scroll.** Some tables genuinely cannot fit a phone, and a ten-column table
   scrolling sideways is correct — far better than ten columns wrapped into vertical mush.

**Never hide, drop or move a column, value or button into an expanded row to stop a table
scrolling.** Every column stays visible at every width. A table that does not fit scrolls sideways
inside its own `overflow-x-auto` wrapper (UB-2, UB-8, UB-21).

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

- **iPad portrait (768–1023px) is narrow too.** Most apps switch row variants at `md:` (768px), so
  the *desktop* row shows on an iPad. It gets the compact tracks through `lg:`-gated classes
  (compact by default, `lg:` restores the `fr` template), so 1024px and up does not change.
- **Header, rows and footer are separate grids, so they share one template string**, built once
  from the visible columns. "Hug" means fixed px tracks sized to each column's longest real value,
  not `max-content` (which comes out a different width per row). The name column is the one
  `minmax(min,1fr)` track.

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

**Derive the minimum, don't guess it.** Keep the per-column minimums in the shared column list
that drives the headers, and sum them in a helper; a hand-typed `min-w-[768px]` goes stale the
moment a column is added. In a CSS grid, each track is `minmax(min, grow)`. One wrapper holding
both a mobile and a desktop row is sized to whichever needs more.

```tsx
// ✓ — minimum derived from the columns themselves
<div className="w-full overflow-x-auto">
  <div className="w-full" style={{ minWidth: tableMinWidth(visibleColumns) }}>

// ✗ — hand-typed minimum, stale the next time a column is added
<div className="overflow-x-auto"><table className="min-w-[768px]">
```

#### Alignment — left, always

**Headers, their body cells, and the totals row are ALL left-aligned.** Every column reads as one
straight vertical edge from heading to total. Right-aligned numbers under a left-aligned heading is
the most common cause of a table that "looks off" with no obvious reason why.

- Define alignment **once per column** in a shared column list; the header cell, body cell and
  footer total cell all read that one alignment set. Never hand-write `text-right` on a cell — that
  is exactly how a header and its column drift apart.
- **No per-cell nudges.** `pl-24`, `-ml-6`, `pl-16` and friends are banned. If a heading does not
  sit over its data, the grid tracks are wrong — fix the track, not the padding. An element that
  needs its own position (an expand caret) gets **its own column**; it does not squat in its
  neighbour's.

```tsx
// ✓ — one definition drives header, cell and total
const COLUMNS = [{ key: 'amount', label: 'AMOUNT', width: '1fr', align: 'text-left' }]
<div className={col.align}>{col.label}</div>

// ✗ — header nudged by hand to sit over a cell it does not share a track with
<div className="pl-24">DESIGN</div>
```

#### Currency: the `$` lines up with the heading

A left-aligned money cell starts its `$` at the same x as the first letter of its header. That is
free when the cell and header share a track and the same horizontal padding, with no nudges.

- Same `px-*` on the header cell and the body cell. Set it once on the row, not per cell.
- `tabular-nums` on every money and quantity column (UB-27), so the figures form a clean block.
- In a static cell, keep the `$` **inside the same text node** as the number (`$12.50`), never as a
  separately positioned prefix element — a floated or absolutely positioned `$` cannot stay aligned.
- A range (`$5.25 - $6.50 & up`) starts at that same left edge; give the column the 110px minimum
  so it does not wrap mid-range.

```tsx
// ✓ — $ is the first glyph of a left-aligned cell on a shared track
<div className="text-left tabular-nums">{formatCurrency(amount)}</div>

// ✗ — right-aligned, so the $ sits at a different x on every row
<div className="text-right">{formatCurrency(amount)}</div>
```

**Editable money cell.** A number input cannot hold the `$` in its value without breaking the
parent's parse, so the `$` is the input's own prefix (HeroUI `startContent`, or a `<span>` inside
the same flex box for a plain or shadcn `Input`). Prefix and input are left-aligned with no gap, so
the `$` lands on the header's first-letter x like a plain money cell, and the pair is at least
`88px` wide so `$1,234.56` fits without clipping.

```tsx
// ✓ — $ prefix at the cell's left edge; wide enough for 1234.56
<Input startContent="$" className="min-w-[88px]" classNames={{ input: "text-left tabular-nums" }} />

// ✗ — a w-10 input on a 72px track clips "$ 12.75"
<Input startContent="$" className="w-10" />
```

#### In-cell buttons need their own gutter

A cell with an info/help/action button must not let that button crowd the next column.

- `inline-flex items-center gap-1.5` between the value and the button.
- **At least `pr-3` (12px) after the button**, on top of the row gutter, so the icon never visually
  belongs to the column on its right.
- `shrink-0` on the icon so a long value never squeezes it.
- The button keeps its 44px touch target (UB-15) through padding, not by growing the icon.

```tsx
// ✓
<div className="flex items-center gap-1.5 pr-3 text-left tabular-nums">
  <span>{formatCurrency(price)}</span>
  <button className="shrink-0 p-1 rounded hover:bg-(--color-surface)" aria-label="Print details">
    <Info className="w-3.5 h-3.5" />
  </button>
</div>
```

#### Mobile: tables go edge to edge

A table is the one thing allowed to touch the screen edge on a phone (UB-8): every pixel of inset
is a pixel of horizontal scrolling.

- **The container drops its side padding at mobile, and the table fills it:** `px-0 sm:px-6` on
  the modal body / page container. Never `-mx-*` on the child — a negative margin has to be undone
  at every breakpoint and silently clips when a parent gains `overflow-hidden`.
- **Everything that is not a table opts back in** with its own `mx-3 sm:mx-0`.
- **The card around a full-bleed table loses its side border and radius on mobile:**
  `border-y sm:border-x sm:rounded-lg`.
- **Tighten the gutter on mobile** to 4px; column minimums keep columns apart.

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
- Give the scroll container `scrollbarWidth: 'thin'` and a muted thumb.
- A totals row carries one empty cell per column it does not fill, so it stays on the same tracks as
  the rows above. Never span or pad it into position.

#### Inline-edit number cell (edit-in-place in a table)

An in-place editable number cell (qty, price, cost) is ONE reusable compact input used by every
editable numeric column (UB-30), working with a HeroUI or a shadcn `Input`:

- **Aligns with static cells:** `text-left` + `tabular-nums`, inside the same flex wrapper the static
  number uses, so the digits line up exactly (see Alignment above).
- **Quiet at rest, still visibly a field (UB-43):** no heavy border, but an empty cell shows a
  placeholder or a hairline border, and its hit target sits under its header. On focus add a subtle
  highlight + ring from theme variables. HeroUI `variant="flat"` has zero border, so it needs a
  `placeholder`.
- **Sized to the value it must hold:** qty fits 4 digits (48px track); money fits `$1,234.56`
  (88px, see Editable money cell). Never a fixed `w-10` on a money input.
- **Hide native spinners:** `[appearance:textfield] [&::-webkit-inner-spin-button]:appearance-none [&::-webkit-outer-spin-button]:appearance-none`.
- **Mobile fast-entry:** empty the field on focus only below the desktop breakpoint, read from the
  app's viewport hook (`!useIsDesktop()`), never an inline `window.innerWidth`; on blur, if nothing
  was typed, keep the previous value (don't zero it).
- **Keep the parent's logic:** the parent owns the value, `onChange` and `onBlur` (commit).
- Always pass an `aria-label`; use `inputMode="numeric"` (integers) or `"decimal"` (money).

Look for an existing `InlineNumberInput`-style component in the project before writing one (UB-30).
