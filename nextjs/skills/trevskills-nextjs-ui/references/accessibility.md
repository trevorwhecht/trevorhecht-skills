# Accessibility, animation and loading

How the UI behaves for every user: contrast, focus, motion and skeletons. UB-31 and UB-33 to UB-35 are the authority.

## Accessibility

These are correctness requirements, not nice-to-haves.

**Color contrast:** Text meets 4.5:1 against its background (3:1 for large text). Never gray-on-gray. Use CSS variable pairs that are validated together.

**Focus rings:** Never remove the focus ring unless you replace it with a visible custom style.
```tsx
// ✗ — removes all keyboard navigation feedback
className="focus:outline-none"

// ✓ — replaces with visible custom ring
className="focus-visible:ring-2 focus-visible:ring-[var(--color-primary)] focus-visible:outline-none"
```

**Icons:** one SVG icon library, never an emoji as an icon, and an `aria-label` on every icon-only button (UB-31).

**Heading hierarchy:** Never skip heading levels (h1 → h3). One `h1` per page.

**Don't rely on color alone** to convey meaning — pair color with an icon or text label (error state = red + error icon + message, not just red).

## Animation

Keep transitions fast and purposeful. Decorative-only animation is noise.

- **Duration:** 150–300ms for micro-interactions; complex transitions ≤400ms
- **Properties:** Animate `transform` and `opacity` only — never `width`, `height`, `top`, `left` (causes layout reflow)
- **Easing:** `ease-out` for entering elements, `ease-in` for exiting
- **Reduced motion:** Always pair with `motion-reduce:transition-none`
- **Loading states:** a layout-matched skeleton when loading exceeds 300ms; spinners are for action buttons only.
- **Anticipation:** a control shows a pressed state (a small scale-down or darker fill) before the action runs.
- **Follow through:** a moving element may overshoot slightly and settle, kept short.
- **Arcs:** an element that travels across the screen moves on a curve, not a straight line.
- **Secondary action:** an icon or count reacts together with the main change (a cart badge bumps when an item is added).
- **Staging:** one thing moves at a time, and it is where the eye should go.
- **Tap feedback:** every tap shows a visible response; a wait still gets the button spinner (UB-47).
- **Source:** motion rules below marked (WWDC) come from Apple's WWDC 2018 "Designing Fluid Interfaces", Jesse Rurka's reel (https://www.instagram.com/reel/DeW9hxyAMHi/) and the emilkowalski/melvynx Apple-motion skills (skills.sh summary pages only).
- **Respond instantly (WWDC):** a control reacts on pointer down, not on release or after the network call (UB-47).
- **Interruptible (WWDC):** an animation can be grabbed or reversed mid-move; drive it from state (a CSS transition or spring), never a fixed keyframe that must finish first.
- **Redirectable (WWDC):** a new tap during a move retargets from the current position, never snapping back to the start.
- **Velocity carries over (WWDC):** a swipe or drag released while moving continues at that speed; it does not stop dead or restart slow.
- **Springs over curves (WWDC):** gesture-driven motion settles with a spring (damping, no long bounce); fixed-duration easing is for non-gesture changes.
- **Rubber band (WWDC):** dragging past an edge resists in proportion to the distance, never a hard wall.
- **Follow the finger (WWDC):** a dragged element tracks the pointer one to one while held, with no easing lag.
- **Same motion in and out (WWDC):** an element leaves along the path it came in on, and a dismiss gesture matches the open one.

```tsx
// ✓ — performant, respects reduced motion
className="transition-opacity duration-200 ease-out motion-reduce:transition-none"

// ✗ — animating layout properties causes reflow
className="transition-all duration-300"  // never "all"
```

## Skeleton Loaders

Show placeholder bars that match the real layout whenever the UI waits on data — never a bare spinner for content. Spinners are ONLY for action-pending buttons. Every data view also has its empty and error state (UB-33).

**Skeletons are ONLY for dynamic (server/async) data.** Static content — nav labels, headings, sidebars, column titles — renders IMMEDIATELY and is NEVER skeletoned.

**Persistent chrome belongs in `layout.tsx`, not the skeleton.** A static shell element shared across a route's states (a dashboard sidebar, a section header) renders in the route's `layout.tsx`, so it paints instantly and stays mounted; `loading.tsx` covers ONLY the dynamic content area.

**Decouple independent data sources.** Gate each region on its own loading flag; never hold the whole view behind `aLoading || bLoading`.

**Skeletons shimmer.** The primitive animates a light gradient sweep (a `::before` gradient translating across the bar via a `shimmer` keyframe in `globals.css`: `bg-linear-to-r` in Tailwind 4, `bg-gradient-to-r` in Tailwind 3), paired with `motion-reduce:before:animate-none`.

**Primitive:** the project's one skeleton component (shadcn: `src/components/ui/skeleton.tsx`; HeroUI ships `Skeleton`). Its fill is a border-tone theme variable such as `bg-(--color-border)`, never a token that resolves to a text colour.

**Generic composites:** look for shared table, card-grid, form and stat-tile skeletons (e.g. `src/components/shared/skeletons/`) and reuse them before writing bespoke bars.

**Colocated page skeletons:** every data-driven page has a `{Container}-Skeleton.tsx` beside its container, mirroring its real layout — same columns, headers, card shapes.

**Route-level loading:** every dynamic route gets a `loading.tsx` that renders its colocated skeleton; a client page behind `<Suspense>` passes it as the `fallback`:
```tsx
import DashboardSkeleton from "./Dashboard-Skeleton"
export default function Loading() { return <DashboardSkeleton /> }
```

**Keep skeletons in sync:** a layout change updates its colocated skeleton in the same diff (UB-35).
