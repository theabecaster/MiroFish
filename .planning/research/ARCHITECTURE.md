# Architecture Research

**Domain:** SaaS frontend on Vercel calling external simulation backend (Flask/Hetzner)
**Researched:** 2026-03-24
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                        USER BROWSER                                   │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │  Next.js App Router (Client Components + Server Components)    │  │
│  │  React pages: Simulation List / Wizard / Report / Settings     │  │
│  └───────────────────────────┬────────────────────────────────────┘  │
└──────────────────────────────│───────────────────────────────────────┘
                               │ HTTPS fetch
┌──────────────────────────────▼───────────────────────────────────────┐
│                     VERCEL (Next.js)                                  │
│                                                                       │
│  ┌──────────────────────────────────────────────────────────────┐    │
│  │              Next.js Route Handlers (BFF layer)               │    │
│  │                                                               │    │
│  │  /api/simulations   — create, list, status                    │    │
│  │  /api/simulations/[id]/launch  — kick off Flask job           │    │
│  │  /api/analyze-creative  — LLM vision call (user's API key)    │    │
│  │  /api/credits       — balance check                           │    │
│  │  /api/webhooks/stripe — Stripe event handler                  │    │
│  │  /api/auth/callback — Supabase OAuth redirect handler         │    │
│  └──────┬───────────────────────┬───────────────────────────────┘    │
│         │                       │                                     │
│         │ Supabase JS SDK        │ HTTPS + X-Api-Key header           │
└─────────│───────────────────────│─────────────────────────────────────┘
          │                       │
          ▼                       ▼
┌──────────────────┐    ┌──────────────────────────────────────────────┐
│   SUPABASE        │    │           HETZNER CX32 (Flask)               │
│                  │    │                                               │
│  Auth            │    │  POST /api/run-pipeline                       │
│  PostgreSQL DB   │    │    → ontology build                           │
│    simulations   │    │    → Zep graph build                          │
│    reports       │    │    → OASIS simulation subprocess              │
│    credits       │    │    → ReACT report agent                       │
│    users         │    │                                               │
│  Storage         │    │  GET /api/tasks/<task_id>  (status poll)      │
│    creatives     │    │  GET /api/reports/<id>     (fetch result)      │
│  Realtime        │    │                                               │
│    (Postgres     │    │  Writes task status back to Supabase          │
│     Changes)     │    │  via Supabase JS SDK (server-side)            │
└──────────────────┘    └──────────────────────────────────────────────┘
          ▲
          │ Supabase Realtime (WebSocket, Postgres Changes)
          │
┌─────────┴────────────┐
│  Browser (Client     │
│  Component polling   │
│  or Realtime sub)    │
└──────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Implementation |
|-----------|----------------|----------------|
| Next.js Route Handlers | BFF layer — auth guard, credit check, LLM calls, proxy to Flask | `preflight/app/api/` Route Handlers |
| Supabase Auth | User identity, sessions, Google OAuth | `@supabase/ssr` server/client helpers |
| Supabase DB | Persistent state: simulations, reports, credits, user profiles | PostgreSQL via Supabase client |
| Supabase Storage | User-uploaded creative files (images, thumbnails) | Signed upload URLs from Route Handler |
| Supabase Realtime | Push job status changes to browser without polling | Postgres Changes subscription on `simulations` table |
| Flask + MiroFish | All heavy computation — simulation pipeline, Zep, OASIS | Existing backend, minimal new endpoints added |
| Stripe | Credit purchases — Checkout session, webhook fulfillment | Stripe SDK in Route Handlers only |
| LLM (user's key) | Creative analysis (vision), audience builder conversation | Called from Route Handlers using user-stored encrypted key |

## Recommended Project Structure

```
preflight/
├── app/
│   ├── (auth)/
│   │   ├── login/page.tsx           # Supabase email + Google OAuth
│   │   └── callback/route.ts        # OAuth redirect handler
│   ├── (app)/
│   │   ├── layout.tsx               # Auth guard, session provider
│   │   ├── simulations/
│   │   │   ├── page.tsx             # Simulation list
│   │   │   ├── new/page.tsx         # Wizard (steps 1-3)
│   │   │   └── [id]/page.tsx        # Report view + status tracker
│   │   └── settings/page.tsx        # LLM key, profile, billing
│   ├── api/
│   │   ├── simulations/
│   │   │   ├── route.ts             # POST create, GET list
│   │   │   └── [id]/
│   │   │       ├── route.ts         # GET status, DELETE
│   │   │       └── launch/route.ts  # POST → deduct credit → call Flask
│   │   ├── analyze-creative/
│   │   │   └── route.ts             # POST → LLM vision call
│   │   ├── credits/
│   │   │   ├── route.ts             # GET balance
│   │   │   └── checkout/route.ts    # POST → Stripe Checkout session
│   │   └── webhooks/
│   │       └── stripe/route.ts      # POST → verify sig → add credits
│   ├── layout.tsx
│   └── page.tsx                     # Landing / redirect to /simulations
├── components/
│   ├── wizard/                      # Multi-step simulation wizard
│   ├── report/                      # Report rendering components
│   └── ui/                          # shadcn/ui primitives
├── lib/
│   ├── supabase/
│   │   ├── client.ts                # Browser Supabase client
│   │   └── server.ts                # Server Supabase client (cookies)
│   ├── mirofish.ts                  # Flask API client (typed fetch wrapper)
│   ├── llm.ts                       # LLM calls using user's API key
│   ├── stripe.ts                    # Stripe SDK instance
│   └── credits.ts                   # Credit deduct/check helpers
├── types/
│   └── index.ts                     # Shared TypeScript types
└── middleware.ts                    # Auth session refresh on every request
```

### Structure Rationale

- **`app/api/`**: All Route Handlers. Nothing the browser client calls should go directly to Flask or Supabase without passing through here — auth checks and credit deductions live in these handlers.
- **`lib/mirofish.ts`**: Single typed wrapper for all Flask calls. Centralises the `MIROFISH_API_URL` env var and `X-Api-Key` header. Makes it easy to swap the base URL between local dev and Hetzner.
- **`lib/supabase/`**: Two clients — server (uses cookies for SSR) and browser (persists session in localStorage). Using the wrong one in the wrong context is the #1 Supabase/Next.js bug source.
- **`middleware.ts`**: Refreshes Supabase sessions on every request. Required for cookie-based auth with SSR — without it, sessions silently expire.
- **`(auth)/` vs `(app)/`**: Route groups allow different layouts. App group enforces auth at layout level, keeping auth logic out of individual pages.

## Architectural Patterns

### Pattern 1: BFF Proxy with Auth Guard + Credit Gate

**What:** Every simulation launch goes through a Next.js Route Handler that (1) verifies the Supabase session, (2) checks credit balance, (3) deducts one credit atomically, (4) calls Flask, (5) records the pending simulation in Supabase.

**When to use:** Any action that costs credits or touches the Flask backend. The browser never calls Flask directly — this keeps the Flask API key secret and makes credit enforcement server-authoritative.

**Trade-offs:** Adds one hop (Vercel → Flask) but eliminates client-side trust issues. The atomic deduct-then-launch sequence prevents double-spending.

```typescript
// preflight/app/api/simulations/[id]/launch/route.ts
export async function POST(req: Request, { params }: { params: { id: string } }) {
  const supabase = createServerClient()
  const { data: { user } } = await supabase.auth.getUser()
  if (!user) return new Response('Unauthorized', { status: 401 })

  // Atomic credit deduction (returns updated balance or throws if insufficient)
  const { error } = await supabase.rpc('deduct_credit', { user_id: user.id })
  if (error) return Response.json({ error: 'Insufficient credits' }, { status: 402 })

  // Forward to Flask — Flask API key is server-only env var
  const task = await mirofish.post('/api/run-pipeline', { simulationId: params.id, ... })

  // Record pending state in Supabase
  await supabase.from('simulations').update({
    status: 'running',
    flask_task_id: task.task_id
  }).eq('id', params.id)

  return Response.json({ taskId: task.task_id })
}
```

### Pattern 2: Supabase Realtime for Job Status (with Polling Fallback)

**What:** Browser subscribes to Postgres Changes on `simulations` table for the specific row. Flask writes status updates back to Supabase directly (using Supabase service key on the Hetzner server). Browser receives updates via WebSocket without polling.

**When to use:** Simulation status page. Simulations take 2-10 minutes — polling every 5s would work but wastes connections; Realtime is zero-cost on free tier up to 200 concurrent connections.

**Trade-offs:** Realtime requires RLS policies to be correct or clients can subscribe to other users' rows. Polling (`setInterval` + `fetch /api/simulations/[id]`) is the safe fallback for environments where WebSockets are blocked.

```typescript
// components/SimulationStatus.tsx (Client Component)
'use client'
useEffect(() => {
  const channel = supabase
    .channel(`simulation-${id}`)
    .on('postgres_changes', {
      event: 'UPDATE',
      schema: 'public',
      table: 'simulations',
      filter: `id=eq.${id}`
    }, (payload) => setStatus(payload.new.status))
    .subscribe()

  return () => { supabase.removeChannel(channel) }
}, [id])
```

**Flask side** (Hetzner) writes status back:
```python
# backend/app/services/simulation_runner.py
from supabase import create_client
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
supabase.table('simulations').update({'status': 'complete', 'report_id': report_id}).eq('flask_task_id', task_id).execute()
```

### Pattern 3: Stripe Webhook as Single Source of Credit Truth

**What:** Credits are never granted client-side. Only the Stripe webhook Route Handler grants credits, after verifying the Stripe signature. The Checkout success page is cosmetic only — it redirects to the app but does not grant credits.

**When to use:** All credit purchases. This prevents replay attacks and ensures credits are only added when Stripe confirms payment.

**Trade-offs:** Small window (~1-3s) between payment completion and credits appearing — acceptable for this product. Never grant credits on checkout `success_url` redirect.

```typescript
// preflight/app/api/webhooks/stripe/route.ts
export async function POST(req: Request) {
  const body = await req.text()
  const sig = req.headers.get('stripe-signature')!
  const event = stripe.webhooks.constructEvent(body, sig, process.env.STRIPE_WEBHOOK_SECRET!)

  if (event.type === 'checkout.session.completed') {
    const session = event.data.object
    const credits = CREDIT_PACKS[session.metadata.pack_id]
    await supabaseAdmin.rpc('add_credits', {
      user_id: session.metadata.user_id,
      amount: credits
    })
  }

  return new Response(null, { status: 200 })
}
```

## Data Flow

### Simulation Launch Flow

```
User submits Wizard (browser)
    ↓
POST /api/simulations  (Route Handler)
    → Verify Supabase session
    → Upload creative to Supabase Storage (signed URL)
    → LLM vision call (user's API key) → creative JSON profile
    → INSERT simulation row (status: 'draft') → Supabase DB
    ↓
POST /api/simulations/[id]/launch  (Route Handler)
    → Verify session
    → deduct_credit() RPC (atomic, server-side)
    → Build seed document (creative JSON + audience JSON + platform)
    → POST /api/run-pipeline  → Flask (Hetzner)
    → UPDATE simulation row (status: 'running', flask_task_id)
    ↓
Flask pipeline runs (async, Hetzner)
    → ontology → Zep graph → OASIS simulation → ReACT report
    → Writes status updates to Supabase (service key)
    ↓
Supabase Postgres Changes event fires
    ↓
Browser Client Component receives UPDATE via Realtime WebSocket
    → status: 'complete' → redirect to report view
```

### Credit Purchase Flow

```
User clicks "Buy Credits" (browser)
    ↓
POST /api/credits/checkout  (Route Handler)
    → Verify session
    → stripe.checkout.sessions.create({ metadata: { user_id, pack_id } })
    → Return { url: checkoutUrl }
    ↓
Browser redirects to Stripe-hosted Checkout page
    ↓
User pays → Stripe fires checkout.session.completed webhook
    ↓
POST /api/webhooks/stripe  (Route Handler)
    → stripe.webhooks.constructEvent() — signature verification
    → add_credits() RPC → Supabase DB
    ↓
Browser receives credits update via Realtime OR next page load
```

### Settings / LLM Key Storage Flow

```
User enters LLM API key (browser)
    ↓
POST /api/settings/llm-key  (Route Handler)
    → Verify session
    → Encrypt key (AES-256, server-side, key from env)
    → UPDATE user_settings.llm_api_key_encrypted → Supabase DB
    ↓
On simulation launch:
    Route Handler fetches + decrypts key
    Passes plaintext key to Flask as header (or in pipeline payload)
    Key never touches browser after initial save
```

### Key Data Flows Summary

1. **Creative upload:** Browser → Supabase Storage (signed URL, direct upload, bypasses Vercel)
2. **LLM calls:** Route Handler only — user's key decrypted server-side, never returned to browser
3. **Simulation job:** Vercel Route Handler → Flask (HTTPS + API key) → Supabase (Flask writes status back)
4. **Status updates:** Supabase Postgres Changes → Browser WebSocket (Realtime)
5. **Credits:** Stripe webhook → Supabase DB (server-authoritative, no client trust)

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 0-500 users | Current design sufficient. Free tiers cover Supabase Realtime (200 concurrent), Vercel serverless, Hetzner CX32 |
| 500-5K users | Supabase Pro ($25/mo) for more Realtime connections and DB compute. Consider Hetzner CX42 for more concurrent simulations. Simple queue (Supabase pg_cron) if simulation backlog forms. |
| 5K+ users | Simulation jobs need a proper queue (Redis/BullMQ or Inngest). Multiple Hetzner workers. Supabase connection pooling via PgBouncer (built-in on paid tier). |

### Scaling Priorities

1. **First bottleneck:** Hetzner CX32 CPU during concurrent simulations. OASIS subprocesses are CPU-heavy. Fix: vertical scale (CX42) or queue simulations with max concurrency of 2-3.
2. **Second bottleneck:** Supabase Realtime connection limit (200 on free). Fix: upgrade to Pro or fall back all clients to 5s polling when connections are saturated.

## Anti-Patterns

### Anti-Pattern 1: Browser Calling Flask Directly

**What people do:** Skip the Next.js Route Handler and have the browser `fetch(MIROFISH_API_URL)` directly with the API key embedded in client-side env vars (`NEXT_PUBLIC_MIROFISH_API_KEY`).

**Why it's wrong:** `NEXT_PUBLIC_` variables are included in the browser bundle — the API key becomes public. Any user can call Flask endpoints directly, bypassing credit checks entirely.

**Do this instead:** Route Handler validates session + deducts credit + calls Flask with server-only `MIROFISH_API_KEY`. Flask key never reaches the browser.

### Anti-Pattern 2: Granting Credits on Checkout Success Redirect

**What people do:** On the `/checkout/success?session_id=xxx` page, call an API to grant credits based on the session ID in the URL.

**Why it's wrong:** Anyone can construct a success URL with a real session ID (from a previous purchase) and hit the grant endpoint repeatedly. Session IDs are not secrets.

**Do this instead:** Credits are granted exclusively in the Stripe webhook handler after signature verification. The success page is cosmetic.

### Anti-Pattern 3: Polling Flask Directly for Job Status

**What people do:** Browser polls `GET /api/simulations/[id]/status` which calls Flask `GET /api/tasks/<flask_task_id>` on every tick.

**Why it's wrong:** Every poll passes through a Vercel serverless function → Flask HTTP call → response. At 5s intervals, a 10-minute simulation = 120 Flask roundtrips per user, plus 120 Vercel function invocations. Compounds badly with multiple concurrent users.

**Do this instead:** Flask writes status to Supabase. Browser subscribes to Supabase Realtime. Zero polling for status. One HTTP call to fetch the final report when `status = 'complete'`.

### Anti-Pattern 4: Storing User LLM Keys in Plain Text

**What people do:** Save the user's API key as a plain text string in the Supabase `user_settings` table.

**Why it's wrong:** A Supabase misconfiguration, SQL injection, or compromised service key exposes all user keys. LLM API keys often have significant billing authority.

**Do this instead:** Encrypt at rest with AES-256 in the Route Handler before writing to DB. Store `llm_api_key_encrypted` and `llm_api_key_iv`. Decrypt server-side only when needed for a simulation launch.

### Anti-Pattern 5: Vercel Function Timeout on Simulation Launch

**What people do:** POST to Flask from a Route Handler and `await` the entire pipeline response (which takes 2-10 minutes).

**Why it's wrong:** Vercel Hobby tier has a 10s serverless function timeout. Pro has 60s configurable up to 5 minutes. A 10-minute simulation will always time out.

**Do this instead:** Flask pipeline is fire-and-forget. The launch Route Handler POSTs to Flask and gets back a `task_id` immediately (Flask returns 202 Accepted). Flask runs the job in a background thread. Status tracked via Supabase, not the HTTP response.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Flask / MiroFish | HTTPS from Route Handlers. `X-Api-Key` header for auth. Returns `task_id` immediately (async). | `MIROFISH_API_URL` env var switches between `localhost:5001` (dev) and Hetzner (prod). Server-only env var — never `NEXT_PUBLIC_`. |
| Supabase Auth | `@supabase/ssr` with cookie-based sessions. `middleware.ts` refreshes sessions. | Two clients: server (cookies) and browser. Mixing them up causes subtle session bugs. |
| Supabase DB | Row Level Security on all tables. `user_id` foreign key enforced at DB level. Atomic credit operations via Postgres functions (RPCs), not application-level logic. | Use RPC for deduct/add credits to prevent race conditions. |
| Supabase Storage | Signed URLs for upload (browser uploads directly to Supabase, not through Vercel). Route Handler generates the URL, browser does the upload. | Avoids Vercel's 4.5MB request body limit. |
| Supabase Realtime | Client Component subscribes to `postgres_changes` on `simulations` table filtered by `id`. Flask writes status via service key on Hetzner. | RLS must allow authenticated user to SELECT their own simulation row. |
| Stripe | Checkout Sessions for one-time credit purchases. Webhook at `/api/webhooks/stripe` — verify signature before trusting. Credits credited via Supabase RPC. | `STRIPE_WEBHOOK_SECRET` is different for local dev (Stripe CLI) vs production (Stripe dashboard). |
| LLM API (user-provided) | Route Handler decrypts stored key, makes OpenAI SDK-compatible call. Never logged, never returned to client. | Support OpenAI, Anthropic, Gemini via configurable `baseURL`. User picks provider in Settings. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| Browser Client ↔ Next.js Route Handlers | `fetch('/api/...')` | All auth context via cookies (Supabase SSR). No API keys in client. |
| Next.js Route Handlers ↔ Supabase | `@supabase/ssr` server client | Uses service key for privileged ops (webhook credit grants). Uses user session for user-scoped ops. |
| Next.js Route Handlers ↔ Flask | `fetch(MIROFISH_API_URL)` with `X-Api-Key` header | Flask is fire-and-forget for pipeline launch. Status flows back through Supabase, not HTTP response. |
| Flask ↔ Supabase | Supabase Python client with service key | Flask writes `status`, `report_json`, `flask_task_id` to `simulations` table. This is the only path status flows back. |
| Flask ↔ Zep Cloud | Existing MiroFish ZepToolsService | Unchanged from existing backend. |
| Flask ↔ OASIS | Subprocess IPC (existing) | Unchanged. |

## Suggested Build Order

Dependencies between components determine this order. Each step is a prerequisite for the next.

1. **Supabase schema + RLS** — All other components depend on the database schema. Define `simulations`, `reports`, `user_settings`, `credit_transactions` tables. Write RLS policies. Write credit RPCs (`deduct_credit`, `add_credits`). Nothing else can be built correctly without this.

2. **Flask API key auth layer** — Before the Next.js app can call Flask in production, the Flask endpoints need auth. Simple `before_request` decorator checking `X-Api-Key` header. Add `/api/run-pipeline` simplified endpoint. This is a small Flask change but gates all simulation functionality.

3. **Next.js auth scaffolding** — Supabase Auth, `middleware.ts`, login/callback routes, session-aware layouts. Gate everything behind auth before building any features.

4. **File upload + creative analysis** — Supabase Storage signed URLs + LLM vision call Route Handler. The wizard's first step depends on this.

5. **Simulation wizard + launch flow** — Audience builder, seed document construction, the launch Route Handler (credit deduct + Flask call). Depends on #1 (DB), #2 (Flask), #3 (auth), #4 (creative analysis).

6. **Job status tracking** — Flask writes status to Supabase, Realtime subscription on simulation page. Depends on #5 (something must be running to track).

7. **Report view** — Fetch and render the completed MiroFish report. Depends on #6 (status `complete` is the entry point).

8. **Stripe credits** — Checkout session creation, webhook handler, credit balance display. Can be built in parallel with #5-7 but must exist before real users can pay.

9. **Settings page** — LLM key management, profile, billing history. Depends on #3 (auth) and #8 (Stripe) but no other simulation components.

## Sources

- [Next.js Backend for Frontend Guide](https://nextjs.org/docs/app/guides/backend-for-frontend) — official docs, current as of Next.js 16.2.1
- [Next.js Route Handlers](https://nextjs.org/docs/app/getting-started/route-handlers) — official docs
- [Supabase Realtime with Next.js](https://supabase.com/docs/guides/realtime/realtime-with-nextjs) — official docs
- [Supabase Postgres Changes](https://supabase.com/docs/guides/realtime/postgres-changes) — official docs
- [Vercel Function Duration Configuration](https://vercel.com/docs/functions/configuring-functions/duration) — official docs, timeout limits
- [Vercel Function Limitations](https://vercel.com/docs/functions/limitations) — official docs
- [Stripe Webhook Handling with Supabase](https://supabase.com/docs/guides/functions/examples/stripe-webhooks) — official pattern
- [BFF Pattern with Next.js API Routes](https://medium.com/digigeek/bff-backend-for-frontend-pattern-with-next-js-api-routes-secure-and-scalable-architecture-d6e088a39855) — MEDIUM confidence
- [Flask API Key Authentication](https://blog.teclado.com/api-key-authentication-with-flask/) — MEDIUM confidence
- [Long-Running Tasks with Next.js](https://dev.to/bardaq/long-running-tasks-with-nextjs-a-journey-of-reinventing-the-wheel-1cjg) — MEDIUM confidence

---
*Architecture research for: Preflight — Next.js SaaS on Vercel + Flask simulation backend on Hetzner*
*Researched: 2026-03-24*
