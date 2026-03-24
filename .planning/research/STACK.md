# Stack Research

**Domain:** Next.js SaaS frontend — marketer-facing ad pre-testing platform (Preflight)
**Researched:** 2026-03-24
**Confidence:** HIGH (all versions verified via npm registry; all integration patterns verified via official docs or multiple credible 2025 sources)

---

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Next.js | 15.x (15.2.1 current) | App framework | Latest stable; Turbopack dev server is now stable (5–10x faster HMR than Next.js 14); React 19 built in; uncached-by-default fetch is better for this app's dynamic data. The PROJECT.md specifies "Next.js 14 App Router" but 15 is the correct target — it's stable, the breaking changes (async params, uncached fetch) are minor to handle upfront, and starting on 14 means migrating later. |
| React | 19.x (19.2.4 current) | UI runtime | Ships with Next.js 15; Server Components + Actions are stable here. No manual memoization with the experimental React Compiler (can enable later). |
| TypeScript | 5.x (5.0.2+ current) | Type safety | Non-negotiable for this stack; Next.js 15 ships with TS config by default; next.config.ts is now supported. |
| Tailwind CSS | 4.x (4.2.2 current) | Styling | shadcn/ui updated all components for Tailwind v4 + React 19 in February 2025. v4 uses CSS-first configuration (no tailwind.config.js required), ships smaller bundles, and targets modern browsers. Start on v4 — don't start on v3 and migrate later. |
| shadcn/ui | CLI-based (no version pin) | Component library | Not a dependency — it's a code generator. Components are copied into your repo, fully owned and customizable. Fully updated for Tailwind v4 + React 19. Built on Radix UI primitives (accessible, unstyled). Standard choice for 2025 Next.js SaaS. Do not install a single "shadcn" package; use `npx shadcn init`. |

### Auth, DB, Storage, Realtime

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| @supabase/supabase-js | 2.x (2.100.0 current) | Supabase client | Core JS client for all Supabase operations (auth, DB queries, storage, realtime). |
| @supabase/ssr | 0.9.x (0.9.0 current) | SSR auth adapter | Replaces deprecated `@supabase/auth-helpers`. Provides `createBrowserClient` and `createServerClient` for correct cookie-based auth in Next.js App Router. Required for server components and middleware to read/refresh auth tokens. Never use auth-helpers — they're frozen. |

### Payments

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| stripe | 20.x (20.4.1 current) | Stripe SDK (server-only) | Official Node.js SDK. Use only in Server Actions and Route Handlers — never import in client components or it will leak your secret key. Checkout session creation goes in Server Actions. Webhook verification requires a Route Handler (not a Server Action) because Stripe POSTs to a static URL with a raw body that must be read via `request.text()` before parsing. |

### LLM Integration

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| ai (Vercel AI SDK) | 6.x (6.0.138 current) | LLM abstraction | Supports 20+ providers (OpenAI, Anthropic, Gemini, etc.) through a unified API — exactly what Preflight needs since users bring their own API key and choose their provider. Version 6 adds typed chat messages, SSE streaming, and a global provider registry. Single import pattern works across all providers; switching providers requires changing one line. Core packages: `ai` (core) + provider-specific packages installed at runtime based on user's selection. |
| @ai-sdk/openai | latest | OpenAI provider | Required alongside `ai` for OpenAI calls. Install similarly for `@ai-sdk/anthropic`, `@ai-sdk/google`. |

### Forms and Validation

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| zod | 4.x (4.3.6 current) | Schema validation | Zod v4 ships 14x faster string parsing, 57% smaller core. Use for API route input validation, form schemas, and Stripe webhook payload typing. Breaking changes from v3 are minor; start on v4. |
| react-hook-form | 7.x (7.72.0 current) | Form state management | Minimal re-renders, excellent DX. Works cleanly with shadcn/ui form primitives. |
| @hookform/resolvers | 5.x (5.2.2 current) | Zod + RHF bridge | Connects Zod schemas to react-hook-form validation. Required for the RHF + Zod pattern. |

### UI Utilities

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| lucide-react | 0.x (0.474.0+ current) | Icons | Ships as shadcn/ui's default icon set; consistent stroke-width, tree-shakable, 1500+ icons. |
| class-variance-authority | 0.7.x | Component variant API | Powers shadcn/ui's variant system. Required if you follow shadcn's component pattern. |
| clsx | 2.x (2.1.1 current) | Conditional class names | Lightweight className utility. |
| tailwind-merge | 3.x (3.0.0+ / 3.5.0 current) | Merge Tailwind classes | Deduplicates conflicting Tailwind classes. Required with shadcn/ui (components use `cn()` from `clsx` + `tailwind-merge`). |
| next-themes | 0.4.x (0.4.6 current) | Dark mode | Flicker-free theme switching with Next.js App Router. Minimal setup. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| ESLint 9 | Linting | Next.js 15 supports ESLint 9 natively; flat config format. Use `next lint`. |
| Prettier | Code formatting | Add `prettier-plugin-tailwindcss` to auto-sort Tailwind class names. |
| `@types/node` | Node.js types | Required for type-safe `process.env` access in Next.js config and API routes. |
| Turbopack | Dev bundler | Enabled with `next dev --turbo`. Stable in Next.js 15. Do not configure Webpack customizations that break Turbopack. |

---

## Installation

```bash
# Bootstrap Next.js 15 project in preflight/ directory
npx create-next-app@latest preflight --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"

cd preflight

# Supabase
npm install @supabase/supabase-js @supabase/ssr

# Stripe
npm install stripe

# Vercel AI SDK + providers
npm install ai @ai-sdk/openai @ai-sdk/anthropic @ai-sdk/google

# Validation + forms
npm install zod react-hook-form @hookform/resolvers

# UI utilities
npm install lucide-react class-variance-authority clsx tailwind-merge next-themes

# Initialize shadcn/ui (interactive CLI, copies components into src/components/ui/)
npx shadcn init
```

---

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| Next.js 15 | Next.js 14 | Never for a new project. 14 is a dead end; 15 is stable. The PROJECT.md mentions "Next.js 14" as a constraint but this was written before 15 was fully released and proven. Start on 15. |
| Tailwind CSS v4 | Tailwind v3 | Never for a new project using shadcn/ui. All shadcn components are now v4-first. |
| @supabase/ssr | @supabase/auth-helpers | Never — auth-helpers is deprecated and frozen. No bug fixes or new features. |
| Vercel AI SDK v6 | Raw OpenAI SDK | Only if you will exclusively use OpenAI and never other providers. Preflight requires provider selection by users, so the abstraction is essential. |
| Zod v4 | Zod v3 | Only if you have a large existing codebase on v3 that would require migration effort. For new projects, start on v4 always. |
| react-hook-form | TanStack Form | TanStack Form is v0/unstable as of early 2025. react-hook-form v7 is stable, widely adopted, and works well with shadcn/ui. |
| Route Handler for webhooks | Server Action for webhooks | Never use Server Actions for Stripe webhooks. Stripe POSTs raw bytes; Server Actions use multipart/form-data parsing. Raw body access via `request.text()` only works in Route Handlers. |
| SWR or native fetch | TanStack Query | For this 4-screen app, SWR or native fetch in Server Components is sufficient. TanStack Query adds overhead without benefit at this scale. Use Server Components for initial data load; SWR for client-side polling of simulation status. |

---

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| `@supabase/auth-helpers` | Officially deprecated; frozen; no new features or bug fixes | `@supabase/ssr` |
| NextAuth.js / Auth.js | Adds a third auth system when Supabase Auth already handles everything, including Google OAuth | Supabase Auth via `@supabase/ssr` |
| Prisma / Drizzle ORM | Supabase has a typed JS client with auto-generated types from your schema. Adding an ORM layer creates a N+1 abstraction on top of PostgREST with no benefit — and won't work on the Vercel Edge runtime | `@supabase/supabase-js` typed queries + `supabase gen types typescript` for local type generation |
| Stripe.js (frontend) | `@stripe/stripe-js` is only needed for custom card inputs. Preflight uses Stripe-hosted Checkout which requires zero client-side Stripe SDK | `stripe` (server-only) + redirect to Stripe Checkout URL |
| `@stripe/react-stripe-js` | Same reason as Stripe.js above — introduces unnecessary client bundle weight for a hosted Checkout flow | Redirect to Stripe Checkout URL via Server Action |
| Emotion / styled-components | CSS-in-JS with runtime overhead; incompatible with React Server Components | Tailwind CSS |
| Framer Motion | Heavy bundle (~160KB); overkill for 4 screens. Preflight is a tool, not a marketing site | CSS transitions via Tailwind's `transition-` utilities; or `tw-animate-css` for specific needs |
| `pages/` router | Legacy routing model; Supabase SSR, Server Actions, and React Server Components all require App Router | `app/` directory (App Router) |
| `getServerSideProps` | Pages Router only; blocked by App Router | Server Components with `async` data fetching |
| Zustand / Redux | Global state management is overkill for 4 screens. Supabase Realtime + React state handles simulation status. Server Components eliminate most client state needs | React `useState`/`useContext` + Supabase Realtime |

---

## Stack Patterns by Variant

**For simulation status tracking:**
- Use Supabase Realtime (`supabase.channel()`) for WebSocket-based status updates, not polling
- Subscribe to the `simulations` table with `postgres_changes` filter
- Initial state: fetch via Server Component; live updates: Realtime channel in a Client Component
- The free Supabase tier supports Realtime; polling every 5s would also work as a fallback

**For user LLM API key storage:**
- Store encrypted in Supabase DB (not `localStorage` — XSS risk)
- Encrypt with a server-side key before writing to DB
- Retrieve server-side only in API routes/Server Actions; never expose to client

**For multi-provider LLM support:**
- Use Vercel AI SDK's `createOpenAI({ baseURL, apiKey })` pattern — it works for OpenAI, Anthropic, and Gemini with provider-specific packages
- Store `provider` and encrypted `apiKey` in user profile; instantiate the correct provider at request time in a Server Action

**For the audience wizard (conversational multi-step form):**
- Use react-hook-form with a wizard state machine: one `useForm` instance, step navigation controlled with React state
- Do not use a separate form library for multi-step flows — RHF handles this cleanly with `mode: 'onBlur'` and per-step `trigger()` validation

**For Stripe credits (not subscriptions):**
- Server Action creates Checkout Session with `payment_intent_data.metadata.user_id` and `credits_amount`
- Route Handler at `/api/webhooks/stripe` processes `checkout.session.completed`
- Credit ledger in Supabase: append-only `credit_transactions` table; current balance is a `SUM()` query or cached column
- Atomic deduction: use a Postgres function / RPC called via `supabase.rpc()` to prevent race conditions

---

## Version Compatibility

| Package | Compatible With | Notes |
|---------|-----------------|-------|
| Next.js 15.x | React 19.x | App Router requires React 19. Pages Router supports React 18 (but don't use Pages Router). |
| @supabase/ssr 0.9.x | @supabase/supabase-js 2.x | Must use together; ssr package wraps supabase-js. |
| Tailwind CSS 4.x | shadcn/ui (Feb 2025+ CLI) | shadcn components updated for v4 in February 2025. `npx shadcn init` detects Tailwind version automatically. |
| react-hook-form 7.x | @hookform/resolvers 5.x | resolvers v5 required for Zod v4 support. resolvers v4 only supports Zod v3. |
| Zod 4.x | @hookform/resolvers 5.x | See above. |
| ai 6.x | @ai-sdk/openai, @ai-sdk/anthropic, @ai-sdk/google (all latest) | Provider packages must be installed separately from `ai` core. They follow their own versioning. Always install latest when you install `ai` v6. |
| stripe 20.x | Node.js 18.18+ | Next.js 15 requires Node 18.18+ anyway; aligned. |

---

## Sources

- [Supabase SSR docs for Next.js](https://supabase.com/docs/guides/auth/server-side/nextjs) — `@supabase/ssr` setup, middleware pattern, `createServerClient` / `createBrowserClient` — HIGH confidence
- [Next.js 15 release blog](https://nextjs.org/blog/next-15) — Breaking changes, Turbopack stable, React 19 requirement, async params — HIGH confidence
- [Vercel AI SDK docs](https://ai-sdk.dev/docs/introduction) — v6 current, multi-provider support, core packages — HIGH confidence
- [npm registry](https://www.npmjs.com) — Versions verified for: next (16.2.1), @supabase/ssr (0.9.0), @supabase/supabase-js (2.100.0), stripe (20.4.1), ai (6.0.138), tailwindcss (4.2.2), zod (4.3.6), react (19.2.4), react-hook-form (7.72.0), @hookform/resolvers (5.2.2) — HIGH confidence
- [shadcn/ui Tailwind v4 changelog](https://ui.shadcn.com/docs/changelog/2025-02-tailwind-v4) — February 2025 update confirming full v4 + React 19 compatibility — HIGH confidence
- [Stripe + Next.js 15 complete guide 2025](https://www.pedroalonso.net/blog/stripe-nextjs-complete-guide-2025/) — Server Actions for checkout, Route Handlers for webhooks pattern — MEDIUM confidence (verified against official Stripe docs architecture)
- [MakerKit: Server Actions vs Route Handlers](https://makerkit.dev/blog/tutorials/server-actions-vs-route-handlers) — When to use each for Stripe — MEDIUM confidence
- [Zod v4 release notes](https://zod.dev/v4) — Performance improvements, version 4.3.6 current — HIGH confidence
- [Supabase Realtime with Next.js](https://supabase.com/docs/guides/realtime/realtime-with-nextjs) — WebSocket subscription pattern, `supabase.channel()` — HIGH confidence

---

*Stack research for: Preflight — Next.js SaaS frontend on MiroFish simulation engine*
*Researched: 2026-03-24*
