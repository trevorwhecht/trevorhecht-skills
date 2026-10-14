---
description: Scalable and reusable template standards — applies when building or contributing to template projects
---

## Scalable & Reusable Template Standards

These rules apply whenever building from or contributing to the base template project, and should inform any project scaffolded from it.

**Component boundaries — no domain logic in shared components:**
- `components/ui/` = fully generic, zero domain assumptions, props-only, no hardcoded strings or business rules
- `components/layout/` = nav, footer, wrappers — generic structure, no project-specific content baked in
- `components/[feature]/` = domain-specific; never bleeds into ui/ or layout/
- If a component imports a domain model, a service, or a hardcoded label — it does not belong in ui/ or layout/

**Framework isolation — keep Next.js at the edges:**
- Server components, route handlers, and middleware live at the route layer only
- Business logic and shared utilities must not import Next.js internals (`next/headers`, `next/navigation`, etc.)
- This makes logic portable and framework upgrades surgical rather than systemic

**Theming via CSS variables, not raw Tailwind values:**
- All colors, spacing tokens, and font sizes that are project-specific live as CSS variables in `globals.css`
- Components reference variables (`bg-[var(--color-primary)]`), not hardcoded Tailwind palette classes
- When Tailwind releases a new major version, the theme is one file to update

**Folder structure — always use `src/`:**
- All app code lives under `src/` — this is non-negotiable for the template
- `@/` always resolves to `src/` so cross-project imports are consistent

**Future-proofing checklist for the template:**
- Exact version pins in `package.json` (no `^` on major framework deps) so upgrades are deliberate
- No use of unstable or internal framework APIs — only documented, stable APIs
- Each major component/feature should work with a mock data prop so it can be tested in isolation without a live DB or auth session
- When a Next.js or React upgrade ships, the upgrade surface should be: route handlers, middleware, and any server component boundaries — nothing else
