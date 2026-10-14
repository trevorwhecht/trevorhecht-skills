---
name: trevskills-twilio-email-setup
description: Use when setting up or debugging Twilio notifications (email, SMS, or both) in a Next.js project. Covers env vars, domain authentication, correct API request formats, notification settings schema, and common 400 errors. Specify "email", "SMS", or "both" when invoking.
---

# Twilio Notifications Setup

## Overview

Specify which channel you need: **email**, **SMS**, or **both**.

Shared credentials (`TWILIO_ACCOUNT_SID` + `TWILIO_AUTH_TOKEN`) power both channels. Email uses the Twilio Comms API via raw fetch. SMS uses the `twilio` npm SDK.

> ⚠️ Email lives in `1console.twilio.com` — NOT the legacy `console.twilio.com`. The legacy console points you to SendGrid; ignore it.

---

## Shared Credentials

```bash
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
```

Add to `.env.local` (dev) and Vercel environment variables (prod). **Restart the dev server after editing `.env.local`** — Next.js only reads env files on startup.

---

## Email Setup

### 1. Domain Authentication (1console only)

`1console.twilio.com` → Products & Services → Email → Domains → Add domain (e.g. `yourdomain.com`). Add the 4 generated DNS records to your DNS provider:

| Type | Host | Value |
|------|------|-------|
| CNAME | `s1._domainkey.yourdomain.com` | `s1.domainkey.uXXX.wl087.sendgrid.net` |
| CNAME | `s2._domainkey.yourdomain.com` | `s2.domainkey.uXXX.wl087.sendgrid.net` |
| CNAME | `em5055.yourdomain.com` | `uXXX.wl087.sendgrid.net` |
| TXT | `_dmarc.yourdomain.com` | `v=DMARC1;p=none;` |

Once all 4 show **Enabled**, you can send from any `@yourdomain.com` address.

### 2. Email Env Vars

```bash
TWILIO_FROM_EMAIL=notifications@yourdomain.com
TWILIO_FROM_NAME=Your App Name   # optional — display name in email client
```

### 3. `emailService.ts`

```ts
export function parseEmailRecipients(raw: string | null | undefined): string[] {
  if (!raw) return []
  return raw.split(/[\n,]+/).map((s) => s.trim()).filter(Boolean)
}

export async function sendEmail(
  recipients: string[],
  subject: string,
  body: string,
): Promise<{ data: boolean; error: string | null }> {
  const accountSid = process.env.TWILIO_ACCOUNT_SID
  const authToken = process.env.TWILIO_AUTH_TOKEN
  const from = process.env.TWILIO_FROM_EMAIL
  const fromName = process.env.TWILIO_FROM_NAME ?? "Your App Name"

  if (!accountSid || !authToken || !from) {
    return { data: false, error: "Email env vars not configured" }
  }
  if (recipients.length === 0) {
    return { data: false, error: "No recipients" }
  }

  try {
    const res = await fetch("https://comms.twilio.com/v1/Emails", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Basic ${Buffer.from(`${accountSid}:${authToken}`).toString("base64")}`,
      },
      body: JSON.stringify({
        from: { address: from, name: fromName },        // name is REQUIRED
        to: recipients.map((address) => ({ address })), // field is 'address' not 'email'
        content: {
          subject,
          text: body,
          html: `<pre style="font-family:sans-serif;white-space:pre-wrap">${body}</pre>`,
        },                                               // both html AND text required
      }),
    })
    if (!res.ok) {
      const text = await res.text()
      console.error("Twilio sendEmail error:", res.status, text)
      return { data: false, error: `Twilio email error: ${res.status}` }
    }
    return { data: true, error: null }
  } catch (err: any) {
    console.error("Twilio sendEmail error:", err?.message ?? err)
    return { data: false, error: err?.message ?? "Unknown email error" }
  }
}
```

### Email API Gotchas (all caused real 400 errors)

| Field | ❌ Wrong | ✅ Correct |
|-------|---------|-----------|
| `from` | `"from@example.com"` (plain string) | `{ address: "...", name: "..." }` |
| `from.name` | omitted | **Required** — 400 without it |
| `to[].field` | `{ email: "..." }` | `{ address: "..." }` |
| `content` | `{ subject, text }` | `{ subject, text, html }` — both required |
| `subject` | top-level field | Must be nested inside `content` |

---

## SMS Setup

### 1. Get a Twilio Phone Number

`1console.twilio.com` → Phone Numbers → Buy a number. Ensure it has SMS capability.

### 2. SMS Env Var

```bash
TWILIO_FROM_NUMBER=+12085551234   # E.164 format — the Twilio number you bought
```

### 3. `twilioService.ts`

Uses the `twilio` npm SDK (not raw fetch):

```ts
import twilio from "twilio"

export async function sendSms(
  to: string,
  body: string,
): Promise<{ data: boolean; error: string | null }> {
  const accountSid = process.env.TWILIO_ACCOUNT_SID
  const authToken = process.env.TWILIO_AUTH_TOKEN
  const from = process.env.TWILIO_FROM_NUMBER

  if (!accountSid || !authToken || !from) {
    return { data: false, error: "Twilio env vars not configured" }
  }

  try {
    const client = twilio(accountSid, authToken)
    await client.messages.create({ from, to, body })
    return { data: true, error: null }
  } catch (err: any) {
    console.error("Twilio sendSms error:", err?.message ?? err)
    return { data: false, error: err?.message ?? "Unknown Twilio error" }
  }
}
```

Phone numbers must be in **E.164 format** (e.g. `+12085551234`). Store in the DB as-is; validate on input in the Settings UI.

---

## Notification Settings Schema (both channels)

```prisma
model NotificationSettings {
  id              Int      @id @default(1)
  smsEnabled      Boolean  @default(false)
  smsPhone        String?                    // E.164 recipient number
  emailEnabled    Boolean  @default(false)
  emailRecipients String?                    // comma/newline-separated addresses
  onNewOrder      Boolean  @default(true)
  onStateChange   Boolean  @default(true)
  onPayment       Boolean  @default(true)
  updatedAt       DateTime @updatedAt
  updatedBy       String?

  @@map("notification_settings")
}
```

After modifying schema: `npx prisma migrate dev --name <name>` (local), then `npx dotenv-cli -e .env.prod -- prisma migrate deploy` (prod).

---

## Fire-and-Forget Pattern (route handlers)

Notifications must never block the HTTP response. Both channels follow the same pattern:

```ts
const ns = await prisma.notificationSettings.findUnique({ where: { id: 1 } })

// SMS
if (ns?.smsEnabled && ns.onNewOrder && ns.smsPhone) {
  sendSms(ns.smsPhone, `New quote #${order.id}. Open dashboard.`).catch(() => {})
}

// Email
const emailRecipients = parseEmailRecipients(ns?.emailRecipients)
if (ns?.emailEnabled && ns.onNewOrder && emailRecipients.length > 0) {
  sendEmail(emailRecipients, `New Quote #${order.id}`, body).catch(() => {})
}

return NextResponse.json({ data: result, error: null }) // never delayed
```

---

## Debugging 400 Errors

Temporarily await and log to see what's failing:

```ts
console.log("[debug]", {
  emailEnabled: settings?.emailEnabled,
  emailRecipients: settings?.emailRecipients,
  TWILIO_FROM_EMAIL: process.env.TWILIO_FROM_EMAIL ? "SET" : "MISSING",
  TWILIO_ACCOUNT_SID: process.env.TWILIO_ACCOUNT_SID ? "SET" : "MISSING",
})
const result = await sendEmail(recipients, subject, body)
console.log("[debug] sendEmail result:", result)
```

| Error | Cause | Fix |
|-------|-------|-----|
| `Invalid value for field 'from'` | Missing `name` in from object | Add `name: "..."` |
| `Invalid value for field 'content'` | Missing `html` | Add `html` alongside `text` |
| `Email env vars not configured` | Env var missing or unsaved | Save `.env.local`, restart dev server |
| `No recipients` | `emailRecipients` null in DB | Set addresses in Settings UI |
