---
name: trevskills-nextjs-ui
description: Use when building any frontend UI component, page, or feature in a Next.js project with Tailwind CSS and a component kit (HeroUI or shadcn/ui). Covers component selection, modal patterns, tables, styling rules, layout, accessibility, and mobile responsiveness.
---

# Next.js UI Development

## Overview

Kit-first, modal-first, mobile-first UI for Next.js + Tailwind apps. The apps use either HeroUI or shadcn/ui (check `package.json` for `@heroui/react`, or `components.json` for shadcn) and either Tailwind 3 or 4; where a rule differs by kit or version, the rule names both. Use the kit's primitives before building custom.

`ui-behaviour.md` (the UB rules) decides whether a screen works and wins over anything here. Where this skill only repeats a UB rule it points at the UB id instead.

Load only the reference file the change touches (see Index).

## Style Guide

Before writing any UI code, check for `.claude/rules/ui-theme.md` in the project root. If it exists and has content, it is the authoritative style guide — follow its palette, typography, icon set, and chart conventions exactly. Do not invent visual decisions that conflict with it.

If the file exists but is empty, note that `/ui-ux-pro-max` should be run to fill it in before making foundational style decisions.

## Required Sub-Skills

Only in a shadcn project (it has `components.json`), invoke both before writing UI code:

- `shadcn` — live project context, component rules, CLI workflow
- `nextjs-shadcn` — page structure, client boundaries, Next.js data patterns

A HeroUI project has no sub-skill; read the component's props in `node_modules/@heroui/` (or its theme in `@heroui/theme`) before overriding a default.

## Core Rules

**Kit-first:** Before building any UI element, check what the project's kit and `src/components/shared/` already provide. Never build from scratch what either provides (UB-30).

**Modal-first:** Prefer overlays over page navigation.

| Situation | shadcn | HeroUI |
|-----------|--------|--------|
| New entity creation | `Dialog` | `Modal` |
| Entity detail view | `Dialog` | `Modal` |
| Multi-field edit / side panel | `Sheet` | `Drawer` |
| Destructive action (delete, archive) | `AlertDialog` | the app's confirm modal (UB-19) |
| Success / error feedback | `toast` (Sonner) | the app's toast (Sonner or `addToast`) |
| Card list → detail | Card → `Dialog`, not new route | Card → `Modal`, not new route |

**Inline editing:** Single-field edits happen inline. Multi-field edits open a side panel.

**Nav pattern:**
- Dashboards → Sidebar nav (desktop) / collapsible or bottom nav (mobile)
- Content / marketing sites → Top nav with hamburger on mobile
- Bottom nav: max 5 items, always include icon + text label
- Back navigation must be predictable — preserve scroll position and state when returning

**Copy:** no helper text under labels or inputs (UB-22).

## Index

| File | Covers | Headings |
|---|---|---|
| `references/tables.md` | Data tables: scroll box, minimums, hugging below 1024px, alignment, money and inline-edit cells | `### Tables`, `#### The ladder — when the minimum exceeds the container`, `#### Phones and iPads: columns hug their content`, `#### Long text in a narrow cell: wrap, then shrink, then ellipsis`, `#### When does it "not fit"? — concrete minimums`, `#### Alignment — left, always`, ``#### Currency: the `$` lines up with the heading``, `#### In-cell buttons need their own gutter`, `#### Mobile: tables go edge to edge`, `#### Other rules`, `#### Inline-edit number cell (edit-in-place in a table)` |
| `references/mobile.md` | Phones and iPads: layout findings, viewport hook, review widths, touch, keyboard, zoom | `## Mobile UI`, `### Mobile layout findings`, `#### One viewport hook`, `#### Review widths`, `### Touch Targets`, `### Keyboard Behavior`, `### Scroll Behavior`, `### Input Font Size`, `### Hover-Only Interactions`, `### Edge Spacing` |
| `references/modals.md` | Placement under the nav, shared class strings, safe areas, background scroll | `### Modal Placement — centred when short, pinned under the nav when tall`, `### Modals and Safe Areas` |
| `references/forms.md` | Errors, validation timing, keyboards, autofill, submit and confirm | `## Forms` |
| `references/styling.md` | Theme variables, Tailwind 3 vs 4, shadcn classes, layout, scrollbars, backgrounds | `## No Scrollbars Until the Full Page Is Utilized`, `## Never Transparent Backgrounds`, `## Tailwind 4 + shadcn Compatibility`, `## Styling` |
| `references/accessibility.md` | Contrast, focus, icons, motion, skeleton loaders | `## Accessibility`, `## Animation`, `## Skeleton Loaders` |
| `references/links.md` | Descriptive share URLs and Open Graph images | `## Shareable Links — Descriptive URLs`, `## Shareable Links — Open Graph Metadata` |

## Component Placement

Before creating any new component:
1. Check `src/components/shared/` for an existing match.
2. A near-match exists → extend it with a prop, never build a visual twin (UB-30).
3. New shared components go in the right subfolder: `tables/`, `modals/`, `forms/`, `layout/`.
4. Drop the container prefix when promoting a feature component to shared.

## Quick Reference

| Need | Solution |
|------|----------|
| Data table | `w-full overflow-x-auto` wrapper + `w-full` table, `min-width` derived from column minimums; never hide columns (tables.md) |
| Form inputs | Kit `Input` at `text-base` (mobile.md "Input Font Size") |
| Edit number in a table cell | One shared inline input (tables.md "Inline-edit number cell") |
| Viewport-dependent behaviour | The app's one `useIsDesktop` hook (mobile.md) |
| Color | Theme variable (styling.md "Styling") |
| Touch target | ≥ 44px (UB-15) |
| Full-height container | `min-h-dvh` / `h-dvh` (UB-9) |
| Modal footer buttons | `pb-[max(1rem,env(safe-area-inset-bottom))]` (UB-11) |
| Review | 390, 820 and 1440px, base vs branch, longest real value |
