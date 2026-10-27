# Forms

Input font size and the keyboard are in `mobile.md`.

## Forms

**Error placement:** Always below the related field, never only at the top.

**Validation timing:** Validate on blur, not on every keystroke, and never on first render (UB-41).

**Mobile keyboard type:** Use the right `inputMode` or `type` so mobile shows the correct keyboard:
```tsx
<Input type="email" inputMode="email" />        // email keyboard
<Input type="tel" inputMode="tel" />             // phone keypad
<Input inputMode="decimal" />                    // money
<Input inputMode="numeric" />                    // whole numbers
```

**Autofill:** Use `autoComplete` so the browser/OS can fill in known values (`email`,
`current-password`, `given-name`). A search or combobox input that draws its own results turns it
off (UB-44).

**Submit state — Enter key + spinner:** `<form onSubmit>` + `type="submit"`, pending from
`useTransition`, a spinner while pending (UB-36). The spinner is the app's one shared spinner
component (UB-31), never a fresh `animate-spin` icon.

```tsx
// ✓
const [isPending, startTransition] = useTransition()
<form onSubmit={(e) => { e.preventDefault(); startTransition(async () => { /* save */ }) }}>
  <Button type="submit" disabled={isPending}>{isPending ? <LoadingSpinner /> : null}Save</Button>
</form>

// ✗ — no Enter key, boolean pending, a second spinner
<Button onClick={save}>{saving && <Loader2 className="animate-spin" />}Save</Button>
```

HeroUI's `Button` takes `isLoading` and shows its own spinner; that counts as the shared one only if
the app has no separate spinner component.

**Confirm modals — Enter key support:** the primary action of every confirm modal is `autoFocus`
(UB-36): `AlertDialogAction` in shadcn, the confirm `Button` in a HeroUI `ModalFooter`.

**Destructive actions:** confirm through the project's own confirm modal, never `confirm()` (UB-19).
Use the semantic danger colour and keep the button apart from the primary CTA.
