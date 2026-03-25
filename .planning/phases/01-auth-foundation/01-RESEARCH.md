# Phase 1: Auth & Foundation - Research

**Researched:** 2026-03-24
**Domain:** Next.js 15 App Router, Supabase Auth (SSR), Tailwind CSS v4, dark mode
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Use Tailwind CSS for styling (utility-first, fast iteration, great Next.js integration)
- **D-02:** Visual direction is bold & playful — vibrant gradients, rounded shapes, warm colors. Think Canva/Loom, not Linear/Vercel. Targeting marketers, not developers
- **D-03:** Support both light and dark mode with a toggle. Include system preference detection
- **D-04:** Use a distinctive heading font with personality (e.g., Plus Jakarta Sans, DM Sans, Space Grotesk) paired with a readable body font
- **D-05:** Custom login/signup forms with a prominent "Continue with Google" button. Supabase JS client handles auth behind the scenes — no @supabase/auth-ui-react
- **D-06:** Single /login page with tabs to switch between Sign In and Sign Up
- **D-07:** Email confirmation required before access (confirm-then-access). User must click email link before using the app
- **D-08:** Phase 1 creates auth-related tables only (profiles). Each subsequent phase creates its own tables when needed
- **D-09:** Use Supabase CLI migrations (`supabase migration new` / `supabase db push`). SQL files version-controlled in `supabase/migrations/`
- **D-10:** Minimal auth gate — hero with tagline, value prop, and login/signup CTA. Not a full marketing page
- **D-11:** After login, user sees a placeholder home page with Preflight branding and a "Coming soon" message

### Claude's Discretion
- Font pairing selection within the "distinctive + readable" constraint (D-04)
- Color palette specifics within the "bold & playful, warm colors" direction (D-02)
- Dark mode color adjustments
- Next.js folder structure and routing patterns
- Supabase client initialization approach (SSR vs client-side)
- RLS policy implementation details
- Password reset flow UX details

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| AUTH-01 | User can sign up with email and password | Supabase `signUp()` + PKCE flow + email confirmation route handler |
| AUTH-02 | User can sign up / log in with Google OAuth | Supabase `signInWithOAuth({ provider: 'google' })` + Google Cloud Console config + auth callback route |
| AUTH-03 | User session persists across browser refresh | `@supabase/ssr` middleware refreshes cookies on every request; no re-login needed |
| AUTH-04 | User can reset password via email link | `resetPasswordForEmail()` → email → `/auth/confirm` route → `verifyOtp()` → update password page → `updateUser()` |
| AUTH-05 | All app routes except landing page require authentication | Next.js middleware checks `supabase.auth.getUser()`, redirects unauthenticated users to `/login` |
| INFR-01 | Next.js project with configurable `MIROFISH_API_URL` env var | Env var defined in `.env.local`, read from Next.js API routes (not browser) |
| INFR-02 | All MiroFish API calls go through Next.js API routes | Route handlers in `app/api/` act as proxy; browser never calls Flask directly |
| INFR-03 | Supabase RLS policies on all tables (user can only access own data) | `ALTER TABLE profiles ENABLE ROW LEVEL SECURITY` + USING `(auth.uid() = id)` policies |
| INFR-06 | AGPL-3.0 license, public repo, footer link to GitHub + MiroFish attribution | LICENSE file + footer component |
</phase_requirements>

---

## Summary

Phase 1 creates a brand-new Next.js 15 App Router project (the "Preflight" repo, separate from MiroFish). The core technical work is: scaffolding a modern Next.js 15 project with TypeScript and Tailwind CSS v4, wiring Supabase Auth with both email/password and Google OAuth using the `@supabase/ssr` package (PKCE flow, cookie-based sessions), defining the Supabase `profiles` table with RLS policies via CLI migrations, implementing route protection through Next.js middleware, and establishing the visual foundation (dark mode, typography, color palette) per the bold/playful brand direction.

The two hardest pitfalls in this domain are: (1) using `getSession()` instead of `getUser()` on the server — the former is insecure because it reads from cookies without revalidation, the latter hits Supabase's auth server and is always authoritative; (2) Tailwind CSS v4 removed `tailwind.config.js` for dark mode — dark mode must now be configured with `@custom-variant` in `globals.css`, not a config file. Both pitfalls cause silent failures or security holes that are expensive to fix later.

**Primary recommendation:** Use the official `@supabase/ssr` package (not the deprecated auth-helpers), always validate with `getUser()` on the server, and configure Tailwind dark mode via `@custom-variant` in CSS. Build middleware first — it is the foundation everything else rests on.

---

## Project Constraints (from CLAUDE.md)

Per project `CLAUDE.md`:
- Tech stack (frontend): Next.js 15 App Router, TypeScript — deployed on Vercel
- Backend: Supabase (Auth, DB, Storage, Realtime)
- License: AGPL-3.0 — all source code must be publicly available
- LLM cost: $0 to Preflight — all LLM calls use user's own API key
- Existing MiroFish Vue frontend and Flask API must remain functional and untouched
- "Flask connects to Supabase" is explicitly out of scope — only Preflight backend talks to Supabase

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| next | 16.2.1 | App framework (App Router, file-based routing, middleware) | Locked decision — Vercel deployment |
| @supabase/supabase-js | 2.100.0 | Supabase client for auth calls and DB queries | Official Supabase JS SDK |
| @supabase/ssr | 0.9.0 | Cookie-based SSR client for Next.js (PKCE flow, middleware token refresh) | Required for Next.js App Router SSR auth — replaces deprecated auth-helpers-nextjs |
| tailwindcss | 4.2.2 | Utility-first CSS — locked decision D-01 | Locked decision |
| next-themes | 0.4.6 | Theme provider for dark/light/system toggle with no FOUC | Standard pattern for dark mode in Next.js; suppresses hydration mismatch |
| typescript | 6.0.2 | Type safety | Locked by CLAUDE.md stack |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| @fontsource/plus-jakarta-sans | latest | Self-hosted Google Font for heading typography | Alternative to next/font Google Fonts if avoiding Google CDN |

**Note on fonts:** Use `next/font/google` (built into Next.js) for Plus Jakarta Sans + Inter. This zero-config approach handles font optimization, subsetting, and self-hosting automatically. No separate fontsource package needed.

### Deprecated / Do Not Use

| Package | Status | Use Instead |
|---------|--------|-------------|
| @supabase/auth-helpers-nextjs | DEPRECATED | @supabase/ssr |
| @supabase/auth-ui-react | Excluded by D-05 | Custom forms |
| tailwind.config.js darkMode setting | Removed in Tailwind v4 | @custom-variant in globals.css |

### Installation

```bash
# Create the Preflight repo (new, separate from MiroFish)
npx create-next-app@latest preflight --typescript --tailwind --app --src-dir --import-alias "@/*"
cd preflight

# Add Supabase packages
npm install @supabase/supabase-js @supabase/ssr

# Add dark mode
npm install next-themes

# Initialize Supabase CLI in repo root
npx supabase init
```

**Version verification (confirmed 2026-03-24):**
```bash
npm view next version           # 16.2.1
npm view @supabase/supabase-js version  # 2.100.0
npm view @supabase/ssr version  # 0.9.0
npm view next-themes version    # 0.4.6
npm view tailwindcss version    # 4.2.2
```

---

## Architecture Patterns

### Recommended Project Structure

```
preflight/
├── src/
│   ├── app/
│   │   ├── (auth)/              # Auth route group (no layout shared with app)
│   │   │   └── login/
│   │   │       └── page.tsx     # Sign in / Sign up tabs (D-06)
│   │   ├── (app)/               # Protected route group
│   │   │   ├── layout.tsx       # Checks auth, redirects if logged out
│   │   │   └── dashboard/
│   │   │       └── page.tsx     # Placeholder "coming soon" home (D-11)
│   │   ├── auth/
│   │   │   ├── callback/
│   │   │   │   └── route.ts     # OAuth callback — exchanges code for session
│   │   │   ├── confirm/
│   │   │   │   └── route.ts     # Email confirmation + password reset token verify
│   │   │   └── reset-password/
│   │   │       └── page.tsx     # New password form after email link
│   │   ├── api/                 # Next.js API routes (proxy for MiroFish calls)
│   │   │   └── mirofish/
│   │   │       └── [...path]/
│   │   │           └── route.ts # Proxy: reads MIROFISH_API_URL, forwards to Flask
│   │   ├── layout.tsx           # Root layout with ThemeProvider, fonts
│   │   └── page.tsx             # Public landing page (D-10)
│   ├── components/
│   │   ├── ui/                  # Reusable UI primitives (buttons, inputs, tabs)
│   │   ├── auth/                # LoginForm, SignupForm, GoogleButton, etc.
│   │   └── layout/              # Navbar, Footer, ThemeToggle
│   ├── lib/
│   │   └── supabase/
│   │       ├── client.ts        # createBrowserClient() — for Client Components
│   │       └── server.ts        # createServerClient() — for Server Components, Route Handlers
│   └── middleware.ts             # Session refresh + route protection (MUST be at src/ root)
├── supabase/
│   ├── config.toml              # Supabase CLI config (from supabase init)
│   └── migrations/
│       └── 20260324000000_create_profiles.sql
├── .env.local                   # NEXT_PUBLIC_SUPABASE_URL, NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY, MIROFISH_API_URL
└── middleware.ts                # If NOT using src/ dir — must be at project root
```

**Critical:** `middleware.ts` location depends on `src/` dir usage. With `--src-dir`, it goes in `src/middleware.ts`.

### Pattern 1: Supabase Client Utilities (SSR)

Two distinct clients are required. Browser client cannot set cookies; server client must not be used in client components.

```typescript
// src/lib/supabase/client.ts — Client Components only
import { createBrowserClient } from '@supabase/ssr'

export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!
  )
}
```

```typescript
// src/lib/supabase/server.ts — Server Components, Route Handlers, Server Actions
import { createServerClient } from '@supabase/ssr'
import { cookies } from 'next/headers'

export async function createClient() {
  const cookieStore = await cookies()
  return createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!,
    {
      cookies: {
        getAll() { return cookieStore.getAll() },
        setAll(cookiesToSet) {
          try {
            cookiesToSet.forEach(({ name, value, options }) =>
              cookieStore.set(name, value, options)
            )
          } catch {
            // Server Components can't set cookies — middleware handles this
          }
        },
      },
    }
  )
}
```

**Source:** [Supabase SSR docs](https://supabase.com/docs/guides/auth/server-side/nextjs)

### Pattern 2: Middleware — Session Refresh + Route Protection

```typescript
// src/middleware.ts
import { createServerClient } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'

export async function middleware(request: NextRequest) {
  let supabaseResponse = NextResponse.next({ request })

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY!,
    {
      cookies: {
        getAll() { return request.cookies.getAll() },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value))
          supabaseResponse = NextResponse.next({ request })
          cookiesToSet.forEach(({ name, value, options }) =>
            supabaseResponse.cookies.set(name, value, options)
          )
        },
      },
    }
  )

  // IMPORTANT: Use getUser(), never getSession() — getUser() validates JWT against Supabase server
  const { data: { user } } = await supabase.auth.getUser()

  const url = request.nextUrl.clone()
  const isProtectedRoute = !url.pathname.startsWith('/auth') &&
    url.pathname !== '/' &&
    url.pathname !== '/login'

  if (!user && isProtectedRoute) {
    url.pathname = '/login'
    return NextResponse.redirect(url)
  }

  // Redirect logged-in users away from login page
  if (user && url.pathname === '/login') {
    url.pathname = '/dashboard'
    return NextResponse.redirect(url)
  }

  return supabaseResponse
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)'],
}
```

**Source:** [Supabase server-side auth Next.js](https://supabase.com/docs/guides/auth/server-side/nextjs)

### Pattern 3: Auth Callback Route Handler (OAuth + Email Confirm)

```typescript
// src/app/auth/callback/route.ts — handles Google OAuth code exchange
import { createClient } from '@/lib/supabase/server'
import { NextResponse } from 'next/server'

export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url)
  const code = searchParams.get('code')
  const next = searchParams.get('next') ?? '/dashboard'

  if (code) {
    const supabase = await createClient()
    const { error } = await supabase.auth.exchangeCodeForSession(code)
    if (!error) {
      return NextResponse.redirect(`${origin}${next}`)
    }
  }
  return NextResponse.redirect(`${origin}/auth/auth-error`)
}
```

```typescript
// src/app/auth/confirm/route.ts — handles email confirmation + password reset
import { createClient } from '@/lib/supabase/server'
import { NextResponse, type NextRequest } from 'next/server'
import { type EmailOtpType } from '@supabase/supabase-js'

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const token_hash = searchParams.get('token_hash')
  const type = searchParams.get('type') as EmailOtpType | null
  const next = searchParams.get('next') ?? '/dashboard'

  if (token_hash && type) {
    const supabase = await createClient()
    const { error } = await supabase.auth.verifyOtp({ type, token_hash })
    if (!error) {
      // For password reset: redirect to set-new-password page
      if (type === 'recovery') {
        return NextResponse.redirect(new URL('/auth/reset-password', request.url))
      }
      return NextResponse.redirect(new URL(next, request.url))
    }
  }
  return NextResponse.redirect(new URL('/auth/auth-error', request.url))
}
```

**Source:** [Supabase password-based auth](https://supabase.com/docs/guides/auth/passwords), [PKCE flow](https://supabase.com/docs/guides/auth/sessions/pkce-flow)

### Pattern 4: Google OAuth Sign-In

```typescript
// In a Client Component button handler
import { createClient } from '@/lib/supabase/client'

async function signInWithGoogle() {
  const supabase = createClient()
  const { error } = await supabase.auth.signInWithOAuth({
    provider: 'google',
    options: {
      redirectTo: `${window.location.origin}/auth/callback`,
    },
  })
}
```

**Google Cloud Console steps:**
1. Create OAuth 2.0 Client ID (Web application type)
2. Authorized JavaScript origins: `http://localhost:3000` (dev), `https://your-domain.com` (prod)
3. Authorized redirect URIs: your Supabase callback URL (found in Supabase Dashboard > Authentication > Providers > Google)
4. Paste Client ID + Secret into Supabase Dashboard

**Source:** [Supabase Google OAuth docs](https://supabase.com/docs/guides/auth/social-login/auth-google)

### Pattern 5: Dark Mode (Tailwind v4 + next-themes)

**globals.css** — Tailwind v4 no longer uses `tailwind.config.js` for dark mode:
```css
@import "tailwindcss";

/* Tailwind v4: dark mode via @custom-variant, not tailwind.config.js */
@custom-variant dark (&:where(.dark, .dark *));

@theme inline {
  /* Brand color tokens — planner fills these in */
  --color-brand-primary: oklch(65% 0.25 30);   /* warm coral/orange */
  --color-brand-secondary: oklch(70% 0.20 280); /* purple accent */
}

:root {
  --background: oklch(99% 0 0);
  --foreground: oklch(15% 0 0);
}

.dark {
  --background: oklch(12% 0 0);
  --foreground: oklch(95% 0 0);
}
```

**Root layout** (ThemeProvider must be a client component):
```tsx
// src/app/layout.tsx
import { ThemeProvider } from 'next-themes'
import { Plus_Jakarta_Sans, Inter } from 'next/font/google'

const jakartaSans = Plus_Jakarta_Sans({
  subsets: ['latin'],
  variable: '--font-heading',
  weight: ['400', '600', '700', '800'],
})

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-body',
})

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning className={`${jakartaSans.variable} ${inter.variable}`}>
      <body>
        <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
          {children}
        </ThemeProvider>
      </body>
    </html>
  )
}
```

**Source:** [Tailwind dark mode docs](https://tailwindcss.com/docs/dark-mode), [next-themes GitHub](https://github.com/pacocoursey/next-themes)

### Pattern 6: Supabase Migration — Profiles Table + RLS

```sql
-- supabase/migrations/20260324000000_create_profiles.sql

-- Create profiles table
create table public.profiles (
  id uuid references auth.users(id) on delete cascade primary key,
  full_name text,
  avatar_url text,
  created_at timestamptz default now() not null,
  updated_at timestamptz default now() not null
);

-- Enable RLS — without policies this means "deny all"
alter table public.profiles enable row level security;

-- Users can read only their own profile
create policy "Users can view own profile"
  on public.profiles for select
  to authenticated
  using ((select auth.uid()) = id);

-- Users can insert only their own profile row
create policy "Users can insert own profile"
  on public.profiles for insert
  to authenticated
  with check ((select auth.uid()) = id);

-- Users can update only their own profile
create policy "Users can update own profile"
  on public.profiles for update
  to authenticated
  using ((select auth.uid()) = id)
  with check ((select auth.uid()) = id);

-- Auto-create profile on user signup
create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
  insert into public.profiles (id, full_name, avatar_url)
  values (
    new.id,
    new.raw_user_meta_data ->> 'full_name',
    new.raw_user_meta_data ->> 'avatar_url'
  );
  return new;
end;
$$;

create trigger on_auth_user_created
  after insert on auth.users
  for each row execute procedure public.handle_new_user();
```

**CLI workflow:**
```bash
supabase migration new create_profiles    # creates timestamped file
# paste SQL into the new file
supabase db push                          # apply to remote Supabase project
# or for local dev:
supabase start                            # starts local Supabase stack
supabase db reset                         # applies all migrations fresh
```

**Source:** [Supabase RLS docs](https://supabase.com/docs/guides/database/postgres/row-level-security), [managing user data](https://supabase.com/docs/guides/auth/managing-user-data)

### Anti-Patterns to Avoid

- **Using `getSession()` server-side:** Only validates from cookies without re-checking with Supabase auth server. Use `getUser()` in middleware and server code.
- **Calling `supabase.auth.*` inside Server Components without middleware:** The middleware must run to refresh tokens. Skipping middleware breaks session continuity.
- **Configuring `darkMode: 'class'` in `tailwind.config.js`:** This config no longer exists in Tailwind v4. Use `@custom-variant dark` in CSS.
- **Placing `middleware.ts` in wrong directory:** With `--src-dir`, it must be `src/middleware.ts` not root `middleware.ts`.
- **Setting RLS policies without `for authenticated`:** Without the `to authenticated` scope, anonymous users may match vacuous policies.
- **Not adding `suppressHydrationWarning` to `<html>`:** next-themes modifies the `class` attribute after hydration; without this prop, React logs hydration mismatch warnings.
- **Hardcoding MiroFish API URL in client code:** INFR-02 requires all MiroFish calls go through Next.js API routes. The `MIROFISH_API_URL` env var must NOT be `NEXT_PUBLIC_` prefixed — keep it server-only.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Dark mode without flicker (FOUC) | Script in `<head>` to read localStorage | `next-themes` with `suppressHydrationWarning` | FOUC fix requires injecting a blocking script before paint; next-themes handles this correctly |
| Session refresh on every request | Custom cookie parsing + JWT validation | `@supabase/ssr` middleware | Token refresh timing, cookie scoping, and PKCE code exchange have security edge cases |
| Password reset email link handling | Custom token storage and verification | `supabase.auth.verifyOtp()` | Supabase handles token hash generation, 60-second expiry, and type discrimination |
| Google OAuth PKCE code exchange | Manual `code` → `token` exchange | `supabase.auth.exchangeCodeForSession(code)` | PKCE requires a code verifier stored in cookies from the initial redirect — Supabase manages this |
| Font optimization | Manual subsetting + self-hosting | `next/font/google` | Zero-config subsetting, no network requests to Google CDN at runtime, automatic preloading |

**Key insight:** Every auth problem in this stack has at least one edge case (token expiry, PKCE verifier mismatch, cookie sameSite policy) that the official packages handle and custom code will miss on first pass.

---

## Common Pitfalls

### Pitfall 1: `getSession()` vs `getUser()` on the Server
**What goes wrong:** `getSession()` reads the session from the cookie without calling Supabase's auth server. An attacker who forges a cookie bypasses auth checks.
**Why it happens:** The API name is intuitive; developers reach for it first.
**How to avoid:** Always use `supabase.auth.getUser()` in middleware and server components. Only use `getSession()` client-side where the JWT has already been validated.
**Warning signs:** Middleware that calls `getSession()` will appear to work in dev but is insecure.

### Pitfall 2: Tailwind v4 Dark Mode Config Change
**What goes wrong:** `darkMode: 'class'` in `tailwind.config.js` silently has no effect in Tailwind v4 — dark utilities appear to do nothing.
**Why it happens:** Create-next-app generates a `tailwind.config.js` but Tailwind v4 moved configuration into CSS.
**How to avoid:** Add `@custom-variant dark (&:where(.dark, .dark *));` to `globals.css`. Do not set `darkMode` in config.
**Warning signs:** `dark:` classes have no effect; no errors thrown.

### Pitfall 3: Middleware Location with `src/` Directory
**What goes wrong:** Middleware at the project root is ignored when using `--src-dir`.
**Why it happens:** Next.js looks for `middleware.ts` relative to the directory structure — `src/middleware.ts` when src dir is in use.
**How to avoid:** Confirm middleware path matches `--src-dir` flag used during create-next-app.
**Warning signs:** Auth redirects never fire; all routes accessible regardless of session.

### Pitfall 4: Email Redirect URL Not Whitelisted
**What goes wrong:** After clicking a confirmation or reset email, users land on a Supabase error page.
**Why it happens:** Supabase hosted projects reject redirect URLs not in the allowlist (Dashboard > Authentication > URL Configuration > Redirect URLs).
**How to avoid:** Add `http://localhost:3000/**` (dev) and `https://your-domain.com/**` (prod) to the allowlist before testing email flows.
**Warning signs:** PKCE code exchange fails with "redirect URL not allowed" error.

### Pitfall 5: Trigger on auth.users Not Pulled by `supabase db pull`
**What goes wrong:** `supabase db pull --schema auth` does not include triggers defined on `auth.users`. Migration files in git are missing the trigger.
**Why it happens:** Supabase CLI does not pull the `auth` schema triggers automatically (known CLI issue #3795).
**How to avoid:** Write the trigger SQL manually in the migration file (do not rely on `db pull` to capture it). Keep it in `supabase/migrations/` under version control.
**Warning signs:** `public.profiles` rows not created on new signups after `db reset` or fresh environment.

### Pitfall 6: MIROFISH_API_URL Leaked to Browser
**What goes wrong:** If `MIROFISH_API_URL` is prefixed with `NEXT_PUBLIC_`, the Flask backend URL (and any API secrets) is exposed in client-side JavaScript.
**Why it happens:** Developers mistake "I need to use this in my code" for "I need it public".
**How to avoid:** Keep `MIROFISH_API_URL` as a server-only env var (no `NEXT_PUBLIC_` prefix). Only read it in `app/api/` route handlers. Per INFR-02, the browser never calls Flask directly.
**Warning signs:** `MIROFISH_API_URL` appears in browser network requests or `__NEXT_DATA__` JSON.

---

## Code Examples

### Email + Password Signup (PKCE, confirm-then-access)

```typescript
// Client Component
import { createClient } from '@/lib/supabase/client'

async function handleSignUp(email: string, password: string) {
  const supabase = createClient()
  const { error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      // Must be in Supabase URL allowlist
      emailRedirectTo: `${window.location.origin}/auth/confirm`,
    },
  })
  // On success: user gets confirmation email, cannot log in until confirmed (D-07)
  // On error: display error.message
}
```

### Password Reset Request

```typescript
async function handlePasswordReset(email: string) {
  const supabase = createClient()
  const { error } = await supabase.auth.resetPasswordForEmail(email, {
    redirectTo: `${window.location.origin}/auth/confirm?type=recovery&next=/auth/reset-password`,
  })
}
```

### Update Password (after reset link)

```typescript
// In the reset-password page — user is now authenticated via the token
async function handleUpdatePassword(newPassword: string) {
  const supabase = createClient()
  const { error } = await supabase.auth.updateUser({ password: newPassword })
  if (!error) redirect('/dashboard')
}
```

### Font Loading via next/font

```typescript
// src/app/layout.tsx
import { Plus_Jakarta_Sans, Inter } from 'next/font/google'

const heading = Plus_Jakarta_Sans({
  subsets: ['latin'],
  weight: ['600', '700', '800'],
  variable: '--font-heading',
  display: 'swap',
})

const body = Inter({
  subsets: ['latin'],
  variable: '--font-body',
  display: 'swap',
})
// Apply both variables to <html> element as className
```

### ThemeToggle Component (Mounted Check Required)

```typescript
'use client'
import { useTheme } from 'next-themes'
import { useEffect, useState } from 'react'

export function ThemeToggle() {
  const { theme, setTheme } = useTheme()
  const [mounted, setMounted] = useState(false)

  // Must check mounted — server doesn't know the theme
  useEffect(() => setMounted(true), [])
  if (!mounted) return null

  return (
    <button onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>
      {theme === 'dark' ? 'Light' : 'Dark'}
    </button>
  )
}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `@supabase/auth-helpers-nextjs` | `@supabase/ssr` | 2024 | auth-helpers is deprecated; ssr package is the only supported path for App Router |
| `darkMode: 'class'` in tailwind.config.js | `@custom-variant dark` in globals.css | Tailwind v4 (early 2025) | Config-based dark mode silently fails in v4 |
| `supabase.auth.getSession()` server-side | `supabase.auth.getUser()` | 2024 (security advisory) | getSession is insecure on the server — does not revalidate the JWT |
| Webpack (Next.js default bundler) | Turbopack (now the default) | Next.js 15 | `next dev` uses Turbopack by default; `--webpack` flag to opt out |
| `tailwind.config.js` / `tailwind.config.ts` | CSS-first config via `@import "tailwindcss"` in globals.css | Tailwind v4 | Configuration migrated out of JS config into CSS |

---

## Open Questions

1. **Supabase project already exists or needs creation?**
   - What we know: CONTEXT.md says "Supabase project — needs to be created or configured"
   - What's unclear: Whether the user has an existing Supabase project or starts fresh
   - Recommendation: Plan assumes new project; include `supabase link` step to connect CLI to hosted project

2. **Preflight GitHub repo — exists?**
   - What we know: CONTEXT.md says "`github.com/theabecaster/preflight` — does not exist yet, will be created"
   - What's unclear: Whether to include repo creation and AGPL license file in Phase 1 plan
   - Recommendation: Yes — INFR-06 requires public repo and license. Include `gh repo create` and LICENSE file as Wave 0 tasks.

3. **Email provider for production?**
   - What we know: Supabase local dev uses Mailpit (localhost:54324). Hosted Supabase has a heavily rate-limited default SMTP.
   - What's unclear: Which email provider (Resend, SendGrid, Postmark) will be used for production
   - Recommendation: Phase 1 uses local Mailpit for dev and default Supabase SMTP for initial cloud testing. Defer email provider config to a later phase once domain is confirmed.

4. **Supabase project region?**
   - What we know: Infrastructure is Hetzner (EU). Vercel will likely use Edge closest to users.
   - What's unclear: Supabase region selection
   - Recommendation: Choose EU-West (Frankfurt) to minimize latency from Hetzner to Supabase.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | Next.js scaffold | ✓ | v25.8.1 | — |
| npm | Package installation | ✓ | 11.11.1 | — |
| npx | create-next-app, supabase CLI | ✓ | 11.11.1 | — |
| Supabase CLI | Migration management | ✗ | — | Install via npm: `npm install -g supabase` or `npx supabase` |
| Docker | Supabase local stack (`supabase start`) | Not checked | — | Use hosted Supabase project + skip local stack |
| Git | Version control | Assumed ✓ | — | — |
| GitHub CLI (`gh`) | Repo creation for INFR-06 | Not checked | — | Create repo manually via GitHub UI |

**Missing dependencies with no fallback:** None blocking for cloud-first workflow.

**Missing dependencies with fallback:**
- Supabase CLI: Use `npx supabase` for one-off commands without global install, or install globally as first task
- Docker (for local Supabase): Can skip local Supabase stack and use hosted project for all dev work — slower iteration but unblocking
- GitHub CLI: Repo can be created manually

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | None detected in new repo — Wave 0 must add |
| Config file | none — see Wave 0 |
| Quick run command | `npm run test` (after setup) |
| Full suite command | `npm run test:ci` |

**Note:** This is a new Next.js project. No test infrastructure exists yet. Wave 0 must establish it.

For Phase 1, most behavior is auth flow and UI — integration/E2E testing with Playwright is the natural fit. Unit tests for utility functions (middleware redirect logic, token exchange) are appropriate with Vitest.

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| AUTH-01 | Email+password signup creates user, confirmation email sent | Integration (manual during dev) | Manual — requires email client | ❌ Wave 0 |
| AUTH-02 | Google OAuth button redirects to Google, returns logged in | E2E (manual — OAuth requires browser) | Manual | ❌ Wave 0 |
| AUTH-03 | Session persists after refresh | Integration | `npx playwright test auth/session` | ❌ Wave 0 |
| AUTH-04 | Password reset email sent, link works | Integration (manual) | Manual — requires email client | ❌ Wave 0 |
| AUTH-05 | /dashboard redirects to /login when unauthenticated | Unit (middleware) | `npx vitest run middleware` | ❌ Wave 0 |
| INFR-01 | MIROFISH_API_URL configurable | Unit | `npx vitest run env` | ❌ Wave 0 |
| INFR-02 | MiroFish calls routed through /api/* | Integration | `npx vitest run api-routes` | ❌ Wave 0 |
| INFR-03 | Profiles RLS denies cross-user access | Integration (Supabase test helpers) | Manual SQL verification | ❌ Wave 0 |
| INFR-06 | LICENSE file present, footer has attribution | Smoke | `ls LICENSE && grep 'AGPL' LICENSE` | ❌ Wave 0 |

**Recommendation:** For Phase 1, prioritize manual verification of auth flows (email, OAuth) and a single middleware unit test for protected route redirect. Full E2E automation deferred to a later phase — Playwright setup adds complexity to an already multi-step scaffold phase.

### Wave 0 Gaps

- [ ] Test framework decision: Vitest (unit) + Playwright (E2E) — install and configure
- [ ] `tests/middleware.test.ts` — covers AUTH-05 redirect logic
- [ ] `tests/api-routes.test.ts` — covers INFR-02 proxy behavior
- [ ] `playwright.config.ts` — for E2E tests when auth flow is wired

*(Recommendation: defer Playwright to Phase 2+ and focus Wave 0 on Vitest for unit tests only. OAuth and email flows verified manually during phase execution.)*

---

## Sources

### Primary (HIGH confidence)
- [Supabase SSR docs — Next.js](https://supabase.com/docs/guides/auth/server-side/nextjs) — middleware, client utilities, PKCE flow
- [Supabase password-based auth](https://supabase.com/docs/guides/auth/passwords) — signup, confirm, reset flow
- [Supabase Google OAuth](https://supabase.com/docs/guides/auth/social-login/auth-google) — provider config, callback URL
- [Supabase RLS docs](https://supabase.com/docs/guides/database/postgres/row-level-security) — policy syntax, trigger pattern
- [Supabase managing user data](https://supabase.com/docs/guides/auth/managing-user-data) — profiles table pattern
- [Supabase PKCE flow](https://supabase.com/docs/guides/auth/sessions/pkce-flow) — code exchange, token verifier
- [Next.js installation docs](https://nextjs.org/docs/app/getting-started/installation) — v16.2.1, create-next-app flags, Turbopack default
- [Tailwind CSS dark mode](https://tailwindcss.com/docs/dark-mode) — v4 @custom-variant syntax
- npm registry — package versions verified 2026-03-24

### Secondary (MEDIUM confidence)
- [next-themes GitHub](https://github.com/pacocoursey/next-themes) — ThemeProvider setup, suppressHydrationWarning, mounted check pattern
- [Dave Gray — dark mode Next.js](https://www.davegray.codes/posts/light-dark-mode-nextjs-app-router-tailwind) — flicker prevention pattern
- [Supabase CLI issue #3795](https://github.com/supabase/cli/issues/3795) — confirms auth.users triggers not pulled by db pull

### Tertiary (LOW confidence)
- Multiple community blog posts about Next.js 15 + Supabase auth — patterns consistent with official docs; specifics not independently verified

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — versions confirmed against npm registry 2026-03-24
- Architecture: HIGH — patterns sourced from official Supabase and Next.js docs
- Pitfalls: HIGH — pitfall 1 (getUser vs getSession), 2 (Tailwind v4 dark mode), and 5 (trigger pull) verified against official sources
- Pitfall 4 (email allowlist): MEDIUM — documented in multiple community sources, consistent with Supabase docs behavior

**Research date:** 2026-03-24
**Valid until:** 2026-04-24 (stable libraries; Tailwind v4 is new enough that minor changes possible within 30 days)
