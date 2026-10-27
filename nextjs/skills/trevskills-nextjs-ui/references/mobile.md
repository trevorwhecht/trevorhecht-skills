# Mobile

Phones and iPads. UB section C (UB-8 to UB-17) is the authority; this file adds the how.

## Mobile UI

**Every component must look and function equally well on mobile and desktop. Mobile is not optional — design for the smallest screen first.**

### Mobile layout findings

From phone and iPad bugs in the apps. Table detail is in `tables.md`.

- **Data tables never hide, drop or move columns on phones.** They scroll sideways inside their own
  `overflow-x-auto` box, edge to edge (UB-2, UB-8, UB-21). See tables.md "The ladder" and "Mobile:
  tables go edge to edge".
- **Below 1024px, columns hug their content**: fixed px tracks at the concrete minimums, a 4px
  gutter (`gap-1`), no `fr` slack between number columns. Desktop (1024px+) keeps `fr` fill. iPad
  portrait (768–1023px) counts as narrow: the row variant that shows there (usually the desktop row,
  from `md:`) gets the compact tracks through `lg:`-gated classes. See tables.md "Phones and iPads".
- **Editable money inputs fit `$1,234.56`** (88px) and their `$` prefix sits at the cell's left
  edge, at the same x as the `$` of a plain money cell. See tables.md "Editable money cell".
- **A column's header, body and footer total share one alignment set**, defined once per column in
  the shared column list. Never a per-cell `text-right` or padding nudge. See tables.md "Alignment".
- **One compact row height, one shared table kit.** Rows are only as tall as their content, and
  every table uses the same helpers and theme variables. See tables.md "One shared table kit".

#### One viewport hook

Each app has exactly one viewport hook (`useIsDesktop`, built on `useSyncExternalStore` and
`matchMedia`/`resize`, `false` on the server). Components never read `window.innerWidth` inline and
never keep their own resize effect — that is how two components disagree at 767px.

When the app renders mobile and desktop as separate trees, a control change lands in both (UB-17).

```tsx
// ✓ — one shared hook
const isDesktop = useIsDesktop()

// ✗ — inline read: wrong on the server, stale after a resize, a second source of truth
const isMobile = typeof window !== 'undefined' && window.innerWidth < 768
```

Use CSS breakpoints when only the look changes; the hook only when behaviour differs.

#### Review widths

Review at **390px, 820px and 1440px**, base vs branch side by side, using the longest real value in
each column (the longest name, a four-figure price). 390 and 1440 are the UB pass/fail widths; 820
(iPad portrait) catches the desktop row rendered narrow. Placeholder data hides clipping.

### Touch Targets

Every tappable control is at least 44px both ways (UB-15). Neither kit's default meets it (HeroUI
`md` is 40px, shadcn default is 32px and `lg` 36px): add `min-h-11 min-w-11`, or use HeroUI `size="lg"`. Grow an
icon button by padding, never by growing the icon.

### Keyboard Behavior

The virtual keyboard covers the bottom ~40% of the screen. A focused input must scroll clear of it
(UB-14). The browser does this itself unless an ancestor blocks scrolling.

```tsx
// ✗ — overflow:hidden blocks the browser from scrolling inputs above the keyboard
<div className="h-dvh overflow-hidden">
  <form>...</form>
</div>

// ✓ — the page grows and scrolls; nothing above the form clips it
<div className="min-h-dvh">
  <form>...</form>
</div>
```

Inside a fixed-position container, call `scrollIntoView({ block: 'center' })` on focus after a
300ms wait for the keyboard animation.

**Rules:**
- Never put `overflow: hidden` on any ancestor of a form.
- `h-dvh` / `min-h-dvh`, never `h-screen` (UB-9). `dvh` tracks the visible area as the keyboard and
  URL bar move. Support: MDN Baseline 2022 (viewport units `dvh/svh/lvh`).

### Scroll Behavior

Scrolling is on by default; the page itself scrolls (UB-7). Only change `touch-action` where a
different gesture is intentional. `button, a { touch-action: manipulation }` is set once in
`globals.css` (UB-12), not per button.

```tsx
// Photo / image viewer — allow pinch-zoom, prevent accidental page scroll
<div className="overflow-hidden" style={{ touchAction: 'pinch-zoom' }}>
  <Image fill src={src} alt={alt} className="object-contain" />
</div>

// Map, canvas, custom gesture area — full gesture control
<div style={{ touchAction: 'none' }}>
```

| `touch-action` | When to use |
|---|---|
| *(default)* | Normal scrollable content — never override unless needed |
| `manipulation` | `button, a`, globally (UB-12) |
| `pinch-zoom` | Image/photo viewers — allows zoom, prevents scroll |
| `none` | Custom gesture areas (maps, canvas, drag handles) |

### Input Font Size

Focusing an input below 16px makes iOS Safari zoom the page (UB-13). Use `text-base`. HeroUI `Input`
renders `text-small` (14px) by default, so pass `classNames={{ input: "text-base" }}` or set it once
in a shared input wrapper. shadcn's `Input` already ships `text-base md:text-sm`.

### Hover-Only Interactions

Hover-reveal is gated behind `sm:` (UB-16): `sm:opacity-0 sm:group-hover:opacity-100`.

### Edge Spacing

Content never touches the screen edge: `px-4 md:px-6 lg:px-8`. The one exception is a data table on
a phone, which goes edge to edge while everything beside it keeps its gutter (tables.md "Mobile:
tables go edge to edge"; UB-8).
