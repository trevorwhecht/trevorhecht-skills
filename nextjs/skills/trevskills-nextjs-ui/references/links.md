# Shareable links

URLs and Open Graph previews for any page a user can share. Checked against Next 16 (`next/og`, `generateMetadata`).

## Shareable Links — Descriptive URLs

Shareable links are human-readable in both the URL and the OG metadata.

**URL:** append `?name=` with the entity's name so the URL is self-explanatory:
```tsx
// ✗
`${base}/orders/${order.token}`

// ✓
const label = order.nickname ?? `Order #${order.id}`
`${base}/orders/${order.token}?name=${encodeURIComponent(label)}`
```

**OG title:** `Entity #id — Name | App Name` — never just an ID or bare name.

**Checklist:** URL has `?name=`, `og:title` is fully descriptive, `og:image` uses the `/api/og/` route with a `?v=updatedAt` cache buster, `twitter:card: summary_large_image`. If the project has a `.claude/rules/ui-theme.md` with a "Shareable Links" section, it holds the full patterns.

## Shareable Links — Open Graph Metadata

Any route with a shareable link implements OG metadata so social and messaging previews show a title and image. Two files per shareable entity:

**`app/(pages)/[entity]/[id]/layout.tsx`** — exports `generateMetadata()` that fetches the entity and returns `openGraph` + `twitter` metadata. A layout (not the page) so metadata is server-rendered even when the page is a client component.

**`app/api/og/[entity]/[id]/route.tsx`** — returns a 1200×630 `ImageResponse` from `next/og`, with `Cache-Control: no-store, max-age=0` so previews are not stale after edits.

**Both files:** `export const dynamic = "force-dynamic"` — unless `next.config` enables `cacheComponents`, where every route is dynamic by default and a `dynamic` export is a build error (Next 16 docs, "Migrating to Cache Components").

**Cache buster** — append to the OG image URL in `generateMetadata`:
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

Always provide a fallback image (static file in `/public`) for when the entity is not found.
