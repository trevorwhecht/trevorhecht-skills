# Modals

Placement, safe areas and scroll for modals, sheets and drawers. UB section D (UB-18 to UB-21) is the authority. Which component opens for which job is in SKILL.md "Core Rules".

### Modal Placement — centred when short, pinned under the nav when tall

**Scope this to the breakpoint that has the problem** — usually mobile. Changing desktop too when
only mobile was asked for is a regression. On mobile, one CSS trick satisfies both rules:

- **Short modal → vertically centred** in the space below the navbar.
- **Tall modal → flush under the navbar**, filling down to a small bottom gap.

```tsx
// ✓ HeroUI — mobile gets the new behaviour; every value is sm:-reverted to the component's own default
<Modal
  placement="top-center"                 // => items-start sm:items-center
  scrollBehavior="inside"
  classNames={{
    wrapper: "pt-[var(--app-navbar-height)] pb-2 sm:pt-0 sm:pb-0",
    base: "my-auto max-h-full sm:my-16 sm:max-h-[calc(100%-8rem)]",
  }}
/>
```

**Why `my-auto` and not `items-center`:** auto cross-axis margins absorb free space before
`align-items` applies, so a short modal centres and a tall one falls back to `items-start` against
the top. `items-center` overflows a tall modal both ways and **its top scrolls out of reach**.

**HeroUI defaults that fight this (verified in `@heroui/theme`):**

| Default | What it does | Fix |
|---|---|---|
| `placement="auto"` | `items-end sm:items-center` — **bottom-pins every modal on mobile** | `placement="top-center"` (NOT `"top"`, which top-aligns desktop too) |
| base `my-1 sm:my-16` | on mobile, no relationship to where the nav ends | `my-auto sm:my-16` — override mobile, hand `sm:` straight back |
| `scrollBehavior="inside"` → `max-h-[calc(100%-8rem)]` | on mobile the modal can never fill its space; it stays short and scrolls internally while screen sits empty | `max-h-full sm:max-h-[calc(100%-8rem)]` — same deal |

Every Fix restates the component's own `sm:` value rather than dropping it: overriding a default
for mobile silently changes desktop too unless you put it back.

**shadcn `Dialog`** has no placement prop: it centres with `top-1/2 -translate-y-1/2`. Apply the
same idea on `DialogContent` below `sm:` (`top-[var(--app-navbar-height)] translate-y-0 my-auto`
inside a flex overlay, `sm:` restoring the defaults).

**Never bottom-pin a modal on mobile.** It reads as a dismissed sheet and puts the title furthest
from the thumb. Centred or top-pinned only.

The nav offset reads a token (`--app-navbar-height` on `:root`), never a literal (UB-21). Keep the
token and the navbar's height in sync.

Put all of this in ONE shared module and import it into every modal — copying the class strings per
modal is how half of them end up bottom-pinned again.

**⚠️ A shared class-string constant only works if Tailwind scans the file it lives in.** Otherwise
it produces **no CSS rule at all**, silently, while a component prop beside it still works (the
kit's theme is scanned) — it looks like a half-applied design.

```js
// Tailwind 3 — tailwind.config.ts: add every folder that can hold a class-name string
content: ["./src/app/**/*.{ts,tsx}", "./src/components/**/*.{ts,tsx}", "./src/lib/**/*.{ts,tsx}"]
```
```css
/* Tailwind 4 — scans the project automatically but skips .gitignored paths and node_modules;
   add anything else with @source in globals.css */
@source "../lib";
```

**Verify, don't assume:** build the stylesheet and grep for a fragment of the class (Tailwind
escapes the name):

```bash
npx tailwindcss -i src/app/globals.css -o /tmp/out.css            # Tailwind 3
npx @tailwindcss/cli -i src/app/globals.css -o /tmp/out.css       # Tailwind 4
grep -o "pt-[^{ ]*navbar-height[^{ ]*" /tmp/out.css
```

### Modals and Safe Areas

Footer buttons clear the home indicator (UB-11), which only works when the root layout sets
`viewportFit: 'cover'` (UB-10) — without it every `env(safe-area-inset-*)` is 0. The footer is
`DialogFooter` / `SheetFooter` in shadcn, `ModalFooter` / `DrawerFooter` in HeroUI. Support for
`env(safe-area-inset-*)`: MDN Baseline, widely available.

```tsx
// ✗ — Save may sit under the home indicator
<ModalFooter className="p-4">

// ✓
<ModalFooter className="p-4 pb-[max(1rem,env(safe-area-inset-bottom))]">

// app/layout.tsx
export const viewport: Viewport = { width: 'device-width', initialScale: 1, viewportFit: 'cover' }
```

A full-screen sheet or drawer uses `h-dvh overflow-y-auto` (UB-9) — its viewport genuinely is full.

**The page never scrolls behind an open modal (UB-18).** Both kits lock body scroll, but on iOS a
sideways swipe on a table inside the modal chains to the page. Contain it once in `globals.css`:

```css
/* ✓ — the dialog stops scroll chaining; the HeroUI wrapper never scrolls sideways (UB-21) */
[role="dialog"] { overscroll-behavior: contain; }
[data-slot="wrapper"]:has([role="dialog"]) { overflow-x: hidden; overscroll-behavior: contain; }
```

Put `overscroll-behavior` on the dialog only, not on every `overflow-y-auto` inside it, or each card
swallows the wheel and the modal cannot scroll. Support: MDN Baseline — `overscroll-behavior` 2022,
`:has()` 2023.
