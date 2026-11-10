# HeroUI 2 quirks

Checked against `@heroui/react` 2.7.11 with Tailwind 3 (onewitharts). UB ids are in `~/Developer/repos/.claude/rules/ui-behaviour.md`; read the rule there, it is not restated here. Read the component's props in `node_modules/@heroui/<component>/dist/*.d.ts` and its classes in `node_modules/@heroui/theme/dist/components/<component>.js` before overriding a default.

## Input

- `variant="flat"` (the default) paints only `bg-default-100`; `faded` and `bordered` add `border-medium`. A flat inline table input with no value is invisible, so give it a `placeholder` (UB-43).
- `startContent` / `endContent` put the `$` and `%` inside the box (rule: "Units on money and percent inputs" in `forms.md`). HeroUI has no `prefix` / `suffix` slot of its own, so a shared wrapper maps `prefix` to `startContent`.
- Do not pass `description` or `errorMessage` as helper copy under a field (UB-22). `errorMessage` is for a real validation error only, per `forms.md`.
- `labelPlacement` (`inside`, `outside`, `outside-left`) changes the field's height and gap. Change it on one field and its neighbours look off; set it once on the shared input (UB-6).
- An `<Input>` that draws its own result list gets `autoComplete="off"` and a non-contact `name` (UB-44).

## Select and Autocomplete

Use `Select` for a fixed list and `Autocomplete` for a searchable one. Never a native `<select>` (UB-19). Both come from `@heroui/react`; `Autocomplete` is the one that needs `autoComplete="off"` if you swap in a custom `<Input>` list.

## Modal

- `placement` defaults to `auto`: bottom-aligned below `sm`, centred from `sm` up. `center` and `top-center` stay put on phones.
- Default `base` has `mx-1 my-1` below `sm` and `sm:mx-6 sm:my-16`, so a stock modal is not edge to edge on a phone. Override `base` with zero margins, full width and `rounded-none` below `sm`, and restore the inset at `sm:` (UB-8). `size="full"` is edge to edge at every width (`h-[100dvh]`, `rounded-none`), which is wrong for a desktop dialog.
- `scrollBehavior`: `normal` (default, `overflow-y-hidden` on `base`), `inside` (only the body scrolls, `max-h-[calc(100%_-_8rem)]`), `outside` (the wrapper scrolls). Use `inside` for long forms.
- The page behind is locked by react-aria's `usePreventScroll` in `@heroui/use-aria-modal-overlay`. The theme adds no `overscroll-behavior`, so add `overscroll-contain` to the scrolling body yourself (UB-18).

## Theming

- The `heroui()` plugin in `tailwind.config` generates the theme colours (`primary`, `default`, `content1`, `focus` and so on). Keep `./node_modules/@heroui/theme/dist/**/*.{js,ts,jsx,tsx}` in Tailwind `content`, or the kit's own classes are not emitted.
- Override a colour per theme through `heroui({ themes: { light: { colors }, dark: { colors } } })`, not with a hex or raw palette class in a component (UB-38) and not with `dark:` colour classes (UB-39). Brand tokens in `theme.extend.colors` should avoid HeroUI's keys (`primary`, `default`, ...).
- `classNames={{ ... }}` slots on `Input` (`inputWrapper`, `input`, `label`) and `Modal` (`base`, `wrapper`, `body`) take theme-variable classes only.
