# Project Research Summary

**Project:** Preflight — Marketer-Facing Ad Pre-Testing SaaS on MiroFish
**Domain:** Next.js SaaS frontend wrapping a Flask/MiroFish AI simulation backend
**Researched:** 2026-03-24
**Confidence:** HIGH (stack and pitfalls); MEDIUM (features and architecture)

## Executive Summary

Preflight is a credit-based B2C/B2B SaaS product that exposes MiroFish's multi-agent simulation engine as a marketer-friendly ad pre-testing tool. The product is a Next.js 15 App Router frontend (hosted on Vercel) acting as a Backend-for-Frontend (BFF) layer over the existing Flask backend (on Hetzner), with Supabase handling auth, database state, file storage, and realtime status updates. The correct build pattern is well-established: all browser requests route through Next.js Route Handlers, which enforce authentication, deduct credits atomically, and call Flask as a fire-and-forget job. Flask writes completion status directly back to Supabase via its own service key, and the browser receives updates over a WebSocket Realtime subscription rather than polling the Flask backend.

The competitive positioning is clear: Preflight targets DTC marketers and boutique agencies who find enterprise tools like Zappi, Neurons, and System1 too slow, expensive, or research-jargon-heavy. The key differentiators are conversational audience input (not demographic checkboxes), instant AI simulation (5-15 min versus days for panel-based tools), and a plain-English report with a concrete "what to fix" section — not abstract scores. The BYOK (bring-your-own-key) model with credit-based billing matches the burst-usage pattern of campaign marketers and lowers commitment at onboarding.

The primary risk profile is security-first: this product stores user-provided LLM API keys (which carry billing authority) and handles credit transactions. Three failure modes must be designed out from the start, not retrofitted: Supabase RLS misconfiguration enabling data leakage, unencrypted LLM API key storage, and non-idempotent Stripe webhook handling enabling double-credits. All three are cheapest to address in the foundational database schema phase and will be expensive to recover from if discovered post-launch.

## Key Findings

### Recommended Stack

The stack is modern and well-proven for 2026: Next.js 15 (not 14, which is a dead-end), React 19, Tailwind CSS v4, and shadcn/ui (CLI-based, code-copied components). Supabase handles auth, DB, storage, and realtime in a single platform with `@supabase/ssr` — the deprecated `@supabase/auth-helpers` package must never be used. The Vercel AI SDK v6 is the correct LLM abstraction for this product's BYOK + multi-provider model; raw OpenAI SDK is wrong here. Zod v4 and react-hook-form v7 cover validation and wizard state. Stripe server-only SDK handles credit purchases via Checkout sessions and webhook verification.

**Core technologies:**
- **Next.js 15 + React 19**: App Router framework — Turbopack stable, uncached-by-default fetch matches dynamic data needs
- **Tailwind CSS v4 + shadcn/ui**: CSS-first styling, zero-config, all components updated for v4 in Feb 2025
- **@supabase/ssr**: Auth, DB, storage, and realtime — single platform; replaces deprecated auth-helpers
- **Vercel AI SDK v6**: Multi-provider LLM abstraction — essential for BYOK user-selected provider model
- **Stripe (server-only)**: Credit purchases via Checkout session + webhook fulfillment; never imported client-side
- **Zod v4 + react-hook-form v7 + @hookform/resolvers v5**: Form validation stack; v4/v7/v5 versions required together

See `.planning/research/STACK.md` for full version table and compatibility matrix.

### Expected Features

The product needs 15 P1 features at launch, clustered around four workflows: auth/onboarding, creative upload + analysis, simulation run + status, and report delivery. The feature dependency chain is strict — auth gates everything, LLM key setup blocks simulation, creative analysis feeds the audience wizard, and credits gate simulation start. This ordering is non-negotiable and directly maps to phase sequence.

**Must have (table stakes):**
- Auth (email + Google OAuth) — gates all product functionality
- LLM API key setup with provider picker and test-connection — BYOK model blocks simulation without it
- Creative upload (image, thumbnail, copy) — the primary input surface
- LLM vision creative analysis — removes manual tagging friction
- Conversational audience wizard (3 questions) — the UX differentiator over competitor demographic forms
- Simulation run + stage-labeled status tracking — the product working
- Structured report: summary, sentiment breakdown, key message diagnosis, "what to fix" — the deliverable
- Agent quote excerpts in report — builds trust in AI simulation results
- Simulation history list — return visits require this
- Credit balance display + Stripe purchase flow (3 tiers: 5/$19, 20/$59, 100/$199) — monetization
- Credit auto-refund on simulation failure — removes purchase risk anxiety
- Mobile-responsive design — DTC marketers review reports on mobile
- Explicit error states — prevents churn from silent failures

**Should have (competitive differentiators to ship post-validation):**
- Re-run from existing inputs — reduces iteration friction
- Platform-specific simulation context (TikTok vs Meta vs Instagram) — addresses "results feel generic" feedback
- Shareable report URL (public link) — replaces PDF export with lower implementation cost
- Benchmark phrasing in report ("strong for DTC") — addresses "is this good?" confusion
- Email notification on simulation completion — captures users who navigate away during 5-15 min job

**Defer to v2+:**
- A/B variant side-by-side comparison — two separate runs covers the need at MVP
- Team accounts and sharing — validate solo user segment first
- Attention heatmaps — requires CV model integration outside MiroFish pipeline
- Zapier/API integrations — no validated demand pre-launch

See `.planning/research/FEATURES.md` for full competitor analysis and feature dependency tree.

### Architecture Approach

The architecture is a BFF (Backend-for-Frontend) pattern: the browser calls only Next.js Route Handlers at `/api/*`, which enforce auth + credit checks before proxying to Flask. Flask is fire-and-forget — the Route Handler receives a `task_id` (202 Accepted) immediately and records it; Flask writes completion status back to Supabase directly using a service key. Browser receives status updates via Supabase Realtime (WebSocket postgres_changes subscription), not by polling Flask. All LLM calls, Stripe operations, and Flask calls happen server-side only — no sensitive keys ever reach the browser.

**Major components:**
1. **Next.js Route Handlers (BFF layer)** — auth guard, credit check/deduct, LLM vision calls, proxy to Flask, Stripe webhook processing
2. **Supabase** — auth, PostgreSQL (simulations, reports, credit_transactions, user_settings), Storage (creative files), Realtime (status push)
3. **Flask / MiroFish (Hetzner CX32)** — all heavy computation; pipeline runs in background thread, writes completion to Supabase via service key
4. **Stripe** — credit purchase Checkout session + webhook verification; credits never granted client-side
5. **LLM API (user-provided)** — called exclusively from Route Handlers using decrypted key from Supabase Vault; never touches browser after initial save

See `.planning/research/ARCHITECTURE.md` for file structure, data flow diagrams, and code patterns.

### Critical Pitfalls

Ten pitfalls were identified; five are critical and must be designed into Phase 1 schemas and patterns — they are expensive to retrofit post-launch.

1. **Supabase RLS enabled but no policies created** — every query silently returns empty arrays; SQL editor bypasses RLS making it invisible during dev. Prevention: create SELECT/INSERT/UPDATE/DELETE policies in the same migration as `ALTER TABLE ... ENABLE ROW LEVEL SECURITY`. Test via authenticated SDK client, never SQL editor.

2. **`getSession()` used in server auth checks** — trusts a cookie without re-validating against the Supabase Auth server; spoofable by malicious cookies. Prevention: use `getUser()` in all middleware and API routes for access control; `getSession()` for client-side UX hints only.

3. **User LLM API keys stored in plain text** — any DB breach or RLS misconfiguration exposes keys with significant billing authority. Prevention: use Supabase Vault (`vault.create_secret()` / `vault.read_secret()`). Disable statement logging during Vault writes.

4. **Stripe webhook double-credits on retry** — Stripe retries delivery if handler doesn't return 200 within ~30s; without idempotency a slow handler credits the user twice. Prevention: store `stripe_event_id` with unique constraint; attempt INSERT at start of handler and return 200 without processing if event already exists.

5. **Credit balance race condition (double-spend)** — two simultaneous simulation requests both read sufficient balance and both deduct. Prevention: expose credit deduction as a Supabase RPC (Postgres function with `SELECT FOR UPDATE`) called atomically, never a read-then-write in application code.

6. **Vercel 10-second timeout killing simulation trigger** — any Route Handler that awaits the full MiroFish pipeline result (2-10 min) will 504 on Vercel Hobby tier. Prevention: Flask returns `task_id` immediately (202 Accepted); Next.js records the task ID; status tracked via Supabase, not the HTTP response.

See `.planning/research/PITFALLS.md` for all 10 pitfalls, a "looks done but isn't" checklist, and recovery cost estimates.

## Implications for Roadmap

Based on the dependency chain in FEATURES.md and the build order in ARCHITECTURE.md, six phases emerge. The sequence is determined by hard dependencies: database schema before everything, auth before any feature, LLM key setup before simulation, credits before simulation launch, simulation before report.

### Phase 1: Auth and Database Foundation

**Rationale:** Everything else depends on this. The Supabase schema (simulations, reports, credit_transactions, user_settings tables with RLS), credit RPCs (`deduct_credit`, `add_credits`), and Next.js auth scaffolding (middleware, login/callback, session-aware layout) must exist before a single feature can be built correctly. Three of the five critical pitfalls live here: RLS policies, `getUser()` auth checks, and Supabase Vault for key storage schema design.

**Delivers:** Working auth (email + Google OAuth), protected route layout, DB schema + RLS validated, credit RPC functions, `force-dynamic` on all authenticated pages.

**Addresses features:** Email + OAuth sign-up (table stakes), credit balance data model.

**Avoids pitfalls:** RLS without policies (Pitfall 1), `getSession()` server-side (Pitfall 2), module-level Supabase client (Pitfall 3), ISR JWT cache leak (Pitfall 4), plain-text LLM key schema (Pitfall 8).

### Phase 2: Settings and LLM Key Management

**Rationale:** The BYOK model means no simulation can run until a valid API key is stored and verified. This is the onboarding blocker — shipping it before the simulation wizard prevents a dead-end state where users complete the wizard but cannot run. Supabase Vault integration and the LLM key test-connection endpoint live here.

**Delivers:** Settings page with provider picker (OpenAI, Anthropic, Gemini), encrypted key storage via Supabase Vault, test-connection Route Handler, credit balance display in navigation.

**Addresses features:** LLM API key setup (table stakes — P1 dependency).

**Avoids pitfalls:** Plain-text LLM key storage (Pitfall 8), API key logging in Vercel functions.

### Phase 3: Credits and Stripe Integration

**Rationale:** Credits gate simulation start. Building this before the wizard ensures the purchase flow is production-ready before real users hit the credit check. Stripe webhook idempotency and the atomic credit RPC must be correct before any simulation costs credits.

**Delivers:** Stripe Checkout session creation Route Handler, webhook handler with `stripe_event_id` deduplication, `add_credits` Postgres RPC, credit balance display, 3-tier pricing ($19/$59/$199), credit auto-refund mechanism.

**Addresses features:** Credit purchase flow (table stakes), credit balance display, credit auto-refund on failure.

**Avoids pitfalls:** Stripe webhook double-credits (Pitfall 5), credit balance race condition (Pitfall 6), credits granted on checkout success redirect (Architecture Anti-Pattern 2).

### Phase 4: Creative Upload and Analysis

**Rationale:** Creative analysis feeds the audience wizard (per the FEATURES.md dependency tree). Supabase Storage signed upload URLs avoid Vercel's 4.5MB request body limit. The LLM vision Route Handler uses the user's decrypted API key stored in Phase 2.

**Delivers:** Drag-and-drop / file picker creative upload to Supabase Storage, LLM vision call Route Handler (`/api/analyze-creative`), structured creative JSON profile (format, product, tone, CTA, brand signals), confirmation screen before wizard.

**Addresses features:** Creative upload (table stakes), LLM vision creative analysis (differentiator).

**Avoids pitfalls:** Large file uploads through Vercel (use signed URLs direct to Supabase Storage).

### Phase 5: Simulation Wizard, Launch, and Status Tracking

**Rationale:** This is the product core. Depends on all prior phases: DB (Phase 1), LLM key (Phase 2), credits (Phase 3), creative analysis (Phase 4). The BFF launch pattern (auth check → credit deduct → Flask fire-and-forget → 202 Accepted → task ID stored) and the Realtime status subscription must be implemented correctly here to avoid the Vercel timeout pitfall.

**Delivers:** Conversational audience wizard (3 questions + niche tag library), seed document construction, simulation launch Route Handler (`/api/simulations/[id]/launch`) with atomic credit deduction and fire-and-forget Flask call, simulation status page with Supabase Realtime subscription (with `useEffect` cleanup), stage-labeled progress indicator ("Building graph... Running simulation... Generating report..."), simulation history list, error states for failed simulations.

**Addresses features:** Audience wizard (differentiator), simulation run + status tracking (table stakes), simulation history (table stakes), error messaging (table stakes).

**Avoids pitfalls:** Vercel 10s timeout (Pitfall 7), Flask direct browser calls (Architecture Anti-Pattern 1), Realtime subscription leak (Pitfall 10), credit double-spend (Pitfall 6 — deduction is in the launch Route Handler RPC).

### Phase 6: Report Rendering and Polish

**Rationale:** The report is the product's deliverable. It depends on simulation completion (Phase 5). LLM post-processing of the MiroFish JSON output into marketer-structured sections is the final transformation. Agent quote excerpts are pulled from the simulation JSONL output. Mobile responsiveness is highest priority for the report view (DTC marketers on mobile).

**Delivers:** Structured report view with sections: plain-English summary, sentiment breakdown, key message diagnosis, "what to fix" prioritized list, agent quote excerpts ("what they said"), benchmark phrasing. Mobile-responsive layout. Flask-side Supabase write for `report_json` on completion. Credit auto-refund triggered on `status: 'failed'`.

**Addresses features:** Structured report (table stakes), "what to fix" section (differentiator), agent quote excerpts (differentiator), benchmark phrasing groundwork, mobile-responsive design (table stakes).

**Avoids pitfalls:** Raw MiroFish JSON exposed to users (UX pitfall — always post-process through LLM), no progress indication (UX pitfall — covered in Phase 5 but confirmed complete here).

### Phase Ordering Rationale

- Phases 1-3 are pure foundation: no user-facing simulation workflow is possible without DB schema, auth, and credits in place.
- Phase 2 (settings/LLM key) precedes Phase 3 (credits) because a user who purchases credits but cannot configure their LLM key is immediately stuck — onboarding must not create this dead end.
- Phase 4 (creative analysis) precedes Phase 5 (wizard) because the creative JSON is the first input that feeds the audience wizard — building them in sequence matches the feature dependency tree.
- Phase 6 (report) is the final phase because it has no features that other phases depend on; all dependencies flow into it.

### Research Flags

Phases likely needing deeper research during planning:

- **Phase 5 (Simulation Launch):** Flask endpoint shape for `/api/run-pipeline` needs confirmation against the current MiroFish codebase. The fire-and-forget pattern is architecturally correct but the exact payload (seed document format, task ID response schema) requires reading existing backend code before implementing the Route Handler wrapper.
- **Phase 2 (Supabase Vault):** Vault's `create_secret` / `read_secret` API and statement logging behavior should be verified against the current Supabase Vault documentation — the pgsodium deprecation note in PITFALLS.md suggests the API surface may have changed in 2025.

Phases with standard patterns (skip `/gsd:research-phase`):

- **Phase 1 (Auth + DB):** Supabase SSR + Next.js middleware pattern is well-documented and stable. Standard implementation.
- **Phase 3 (Stripe):** Checkout session + webhook handler with idempotency is a well-documented, stable pattern. PITFALLS.md covers all edge cases.
- **Phase 6 (Report):** LLM post-processing and report rendering are pure application logic. No novel integrations.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All package versions verified via npm registry; official docs cross-referenced for all major integration patterns; version compatibility matrix fully validated |
| Features | MEDIUM | Competitor UX scraped directly; billing patterns from industry analysis; some specifics (e.g., exact benchmark bucket values) inferred from adjacent tools where direct evidence was unavailable |
| Architecture | HIGH | Official docs for all integration patterns (Next.js BFF, Supabase Realtime, Stripe webhooks); fire-and-forget Flask pattern verified against Vercel timeout constraints |
| Pitfalls | HIGH | Multiple independent sources, official documentation cross-referenced; CVE-2025-48757 real incident confirms RLS risk level; Stripe webhook race condition pattern verified against payment processor documentation |

**Overall confidence:** HIGH

### Gaps to Address

- **Flask `/api/run-pipeline` endpoint contract:** The exact request payload shape and response schema (task ID format, error codes) must be validated against the existing MiroFish backend before the simulation launch Route Handler is implemented. Read `backend/app/api/` before building Phase 5.
- **Supabase Vault API current state:** The PITFALLS.md flags pgsodium as deprecated as of 2025. Verify that `vault.create_secret()` / `vault.read_secret()` is the current recommended API before implementing Phase 2 LLM key storage.
- **Pricing validation:** The $19/$59/$199 credit tier pricing is based on industry analysis of adjacent tools (PickFu, similar per-test tools), not validated customer research. Treat as an initial hypothesis to test at launch — be prepared to adjust tiers based on conversion data.
- **Flask Supabase service key configuration:** The architecture requires Flask (on Hetzner) to write simulation status and report data back to Supabase using a service key. This requires the Hetzner environment to be configured with `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` — confirm this is in scope for the backend environment setup phase.

## Sources

### Primary (HIGH confidence)

- [Supabase SSR docs for Next.js](https://supabase.com/docs/guides/auth/server-side/nextjs) — `@supabase/ssr` setup, middleware, `createServerClient` / `createBrowserClient`
- [Next.js 15 release blog](https://nextjs.org/blog/next-15) — Turbopack stable, React 19 requirement, async params
- [Vercel AI SDK docs](https://ai-sdk.dev/docs/introduction) — v6, multi-provider, provider registry
- [npm registry](https://www.npmjs.com) — All package versions verified
- [shadcn/ui Tailwind v4 changelog](https://ui.shadcn.com/docs/changelog/2025-02-tailwind-v4) — v4 + React 19 compatibility confirmed Feb 2025
- [Zod v4 release notes](https://zod.dev/v4) — Performance improvements, v4.3.6 current
- [Supabase Realtime with Next.js](https://supabase.com/docs/guides/realtime/realtime-with-nextjs) — WebSocket subscription, `supabase.channel()`
- [Supabase RLS Docs](https://supabase.com/docs/guides/database/postgres/row-level-security) — Policy structure, WITH CHECK, performance
- [Supabase Vault Docs](https://supabase.com/docs/guides/database/vault) — `vault.create_secret()` / `vault.read_secret()`
- [Vercel Function Duration / Limitations](https://vercel.com/docs/functions/limitations) — 10s Hobby timeout confirmed
- [Stripe Webhook idempotency patterns](https://excessivecoding.com/blog/billing-webhook-race-condition-solution-guide) — deduplication via event ID
- [Next.js Route Handlers](https://nextjs.org/docs/app/getting-started/route-handlers) — BFF pattern, official docs

### Secondary (MEDIUM confidence)

- [Behavio Labs — Ad testing software 2026](https://www.behaviolabs.com/blog/ad-testing-software-what-it-is-how-it-works-the-best-platforms-in-2026) — Feature landscape, competitor mapping
- [Neurons AI](https://www.neuronsinc.com/ad-testing/metrics), [System1](https://system1group.com/test-your-ad), [Zappi](https://www.zappi.io/web/creative-digital/), [PickFu](https://www.pickfu.com/products) — Competitor feature analysis
- [GetMonetizely — SaaS credit pricing](https://www.getmonetizely.com/articles/how-should-you-structure-saas-pricing-for-a-credit-based-model) — Credit tier structure rationale
- [Stripe + Next.js 15 complete guide 2025](https://www.pedroalonso.net/blog/stripe-nextjs-complete-guide-2025/) — Server Actions vs Route Handlers for Stripe
- [BFF Pattern with Next.js API Routes](https://medium.com/digigeek/bff-backend-for-frontend-pattern-with-next-js-api-routes-secure-and-scalable-architecture-d6e088a39855) — Architecture pattern validation

---
*Research completed: 2026-03-24*
*Ready for roadmap: yes*
