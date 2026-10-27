# Styling

UB-7, UB-20, UB-38 and UB-39 are the authority.

## No Scrollbars Until the Full Page Is Utilized

No inner `overflow-y-auto` until the viewport is genuinely full; let the page scroll (UB-7). A
desktop-only constraint such as `overflow-y-auto md:max-h-[calc(100dvh-12rem)]` is fine.

**This is about vertical scroll regions.** It does not apply to the horizontal scroll box a data
table always carries (tables.md; UB-2, UB-21): that wrapper shows no scrollbar until the content
exceeds the table's `min-width`, and removing it clips content instead of preventing scroll.

## Never Transparent Backgrounds

Every card, dialog, sheet, dropdown, popover, tooltip and floating element declares a background
(UB-20). Check for a missing `bg-` whenever you copy a component example.

| Surface | Class |
|---|---|
| Dialog / modal / page content | `bg-(--color-background)` |
| Card / sidebar / dropdown | `bg-(--color-surface)` |

## Tailwind 4 + shadcn Compatibility

**Problem:** shadcn installs CSS variables like `--popover`, `--muted`, `--accent` in `:root`. Tailwind 4 needs `--color-{name}` in `@theme inline` to generate `bg-{name}` / `text-{name}` utilities. Where the names don't match, the shadcn utility classes are silently transparent/missing.

**Rule:** In a Tailwind 4 shadcn project, check that each of these has a `--color-*` entry in `@theme inline`; if it doesn't, use the variable form instead:

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

No `dark:` colour variants: light and dark are values behind one variable (UB-39). Audit copied
shadcn code for these classes before committing (`src/components/ui/`, overlays, dropdowns).

HeroUI apps get their colour utilities (`bg-content1`, `text-default-500`, `text-foreground`) from
the `heroui()` Tailwind plugin, which does generate them; this table does not apply there.

## Styling

**Colours come from theme variables only** — no hex, raw palette class or font name in a component
(UB-38). The variable syntax depends on the Tailwind version:

```tsx
// ✓ Tailwind 4 — shorthand
className="bg-(--color-primary) text-(--color-foreground)"
// ✓ Tailwind 3 (and 4) — arbitrary value
className="bg-[var(--color-primary)] text-[var(--color-foreground)]"
// ✗ — raw palette value
className="bg-blue-600 text-gray-900"
```

The `bg-(--x)` shorthand and `bg-linear-to-r` are Tailwind 4 only. In a Tailwind 3 app they compile
to nothing, with no error.

**Responsive layout — mobile-first:**
```tsx
<div className="flex flex-col md:flex-row gap-4">
<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
<div className="grid grid-cols-[repeat(auto-fit,minmax(250px,1fr))] gap-4">   // fits by content width
```

**Container queries** — when a component should respond to its container, not the viewport:
```tsx
<div className="@container">
  <div className="text-base @lg:text-xl">Scales with container, not screen</div>
</div>
```
Built into Tailwind 4. Tailwind 3 needs the `@tailwindcss/container-queries` plugin; without it the
`@` classes do nothing. Support: MDN Baseline 2023 (CSS container size queries).

**Group hover** — child effects triggered by parent hover, gated for touch (UB-16):
```tsx
<div className="group cursor-pointer">
  <p className="sm:group-hover:text-[var(--color-primary)] transition-colors motion-reduce:transition-none">
```

**Z-index scale** — never arbitrary z-index values. Use a defined scale:
```tsx
// z-0 base · z-10 sticky / floating labels · z-20 dropdowns, popovers
// z-40 modals, dialogs · z-100 toasts · z-[1000] critical overlays (video player, lightbox)
```

**List virtualization** — lists with 50+ items are virtualized (`@tanstack/react-virtual`).

**Images** — always `<Image>` from `next/image`, never raw `<img>`, with its size or aspect ratio
reserved so nothing shifts when it loads (UB-37):
```tsx
<Image src={src} alt={alt} className="aspect-video w-full object-cover" />
```
