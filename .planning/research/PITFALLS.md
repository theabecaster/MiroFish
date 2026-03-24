# Pitfalls Research

**Domain:** Next.js + Supabase + Stripe SaaS wrapping a long-running Flask simulation backend
**Researched:** 2026-03-24
**Confidence:** HIGH (multiple independent sources, official documentation cross-referenced)

---

## Critical Pitfalls

### Pitfall 1: Supabase RLS Tables Created Without Policies (Silent Data Loss)

**What goes wrong:**
RLS is enabled on a table but no policies are created. Every query returns 0 rows — not an error, just silence. The app appears broken with no clear indication why. This was the root cause of a January 2025 mass data exposure (CVE-2025-48757) where 170+ Lovable-built apps leaked databases because RLS was never enabled at all.

**Why it happens:**
Supabase disables RLS by default on new tables. Developers enable it thinking they're done, then wonder why their queries return nothing. The SQL Editor in the Supabase dashboard runs as the `postgres` superuser and bypasses all RLS, so testing there passes while real users see empty results.

**How to avoid:**
- Enable RLS AND create SELECT/INSERT/UPDATE/DELETE policies in the same migration.
- Always include `WITH CHECK` clauses on INSERT and UPDATE policies — without them, users can insert rows with any `user_id`, including others'.
- Test all queries through the Supabase client SDK with a real authenticated test user, never through the SQL editor.
- Add `user_id` indexes on every table that uses `user_id = auth.uid()` in policies — without indexes, a policy causes a full table scan (50ms at 10K rows, timeout at 1M rows).
- Required tables for Preflight: `profiles`, `simulations`, `reports`, `credit_transactions`.

**Warning signs:**
- Queries succeed but return empty arrays when a real user is authenticated.
- SQL editor shows data but the app shows nothing.
- `console.log(data, error)` shows `data: []` with `error: null`.

**Phase to address:** Auth + Database foundation phase (first phase).

---

### Pitfall 2: Supabase `getSession()` in Server Code Trusts Spoofable Cookies

**What goes wrong:**
`supabase.auth.getSession()` is used in Next.js middleware or API routes to protect pages. It reads the session from cookies without re-validating against the Supabase Auth server. A maliciously crafted cookie can bypass protection.

**Why it happens:**
`getSession()` is fast and convenient, so developers default to it everywhere. The security distinction between `getSession()` (reads cookie, no revalidation) and `getUser()` (hits Supabase Auth server every call) isn't obvious from the API surface.

**How to avoid:**
- Use `supabase.auth.getUser()` in all server-side code (middleware, API routes, Server Components) where security matters.
- Reserve `getSession()` for client-side UX hints only (e.g., showing/hiding UI elements), never for access control.
- In Next.js middleware, use `getUser()` to validate before allowing access to protected routes.

**Warning signs:**
- Auth checks in middleware use `getSession()`.
- Direct copy of older Supabase + Next.js tutorials (pre-2024) — they commonly used `getSession()`.

**Phase to address:** Auth + Database foundation phase.

---

### Pitfall 3: Module-Level Supabase Client Causing Session Leakage Between Users

**What goes wrong:**
A Supabase client is initialized at module scope (`const supabase = createClient(...)` outside of the request handler). In serverless environments (Vercel), function instances are reused across requests. User A's session leaks into User B's request — one user sees another user's simulations.

**Why it happens:**
It works in local dev (single user, fresh process each time), and even in early production with low traffic. The failure only manifests under concurrent load when instances are reused.

**How to avoid:**
- Always initialize the Supabase server client inside the request handler function, not at module scope.
- Use the `@supabase/ssr` package's `createServerClient` factory inside each API route / Server Action / Server Component.
- Never share a Supabase client instance across requests.

**Warning signs:**
- `createClient()` call at the top level of an API route file (outside `export default async function handler`).
- Intermittent "wrong user's data" reports that can't be reproduced consistently.

**Phase to address:** Auth + Database foundation phase.

---

### Pitfall 4: ISR-Cached Pages Leaking JWT Tokens via Set-Cookie Headers

**What goes wrong:**
A Next.js page uses Incremental Static Regeneration (ISR) and also triggers a Supabase session refresh. The refreshed JWT is included in the `Set-Cookie` response header. When Next.js caches this response, it serves the cached `Set-Cookie` header to subsequent users — those users' browsers store someone else's JWT token.

**Why it happens:**
ISR and auth are both legitimate features. The interaction between ISR's response caching and cookie-setting headers is a non-obvious footgun not documented prominently.

**How to avoid:**
- Add `export const dynamic = 'force-dynamic'` to every page that requires authentication or touches Supabase sessions.
- Alternatively, never use ISR on authenticated pages — reserve it only for fully public, static content.
- For Preflight, all four screens (Simulation List, New Simulation Wizard, Report View, Settings) are authenticated and must be force-dynamic.

**Warning signs:**
- Deployed pages without `export const dynamic = 'force-dynamic'` on routes behind auth.
- Users occasionally signed in as each other.

**Phase to address:** Auth + Database foundation phase.

---

### Pitfall 5: Stripe Webhook Double-Credit on Retry (No Idempotency Guard)

**What goes wrong:**
Stripe retries webhook delivery if your endpoint doesn't return a 2xx within ~30 seconds. Without idempotency protection, a slow handler that eventually succeeds may have already credited the user on first delivery, then credits them again on retry. Users get free credits; you lose revenue.

**Why it happens:**
Developers handle the happy path but don't account for Stripe's retry behavior. The webhook handler credits the user and then returns 200 — but if there's a slow database write, Stripe retires before the 200 and hits the endpoint again.

**How to avoid:**
- Store each processed `stripe_event_id` in a `stripe_webhook_events` table with a unique constraint.
- At the start of every webhook handler: attempt to insert the event ID. If it already exists (unique constraint violation), return 200 immediately without processing.
- Use a Postgres transaction: insert webhook event ID + credit the user in a single atomic operation. Either both happen or neither does.
- Return 200 immediately after enqueuing the work, not after completing it.
- For the credits table, use `INSERT INTO credit_transactions` — never `UPDATE balance`. A ledger of transactions is auditable and idempotent by design.

**Warning signs:**
- Webhook handler queries the DB to check "did I already process this?" using a SELECT before INSERT (TOCTOU race condition — two requests can both pass the check before either commits).
- No `stripe_webhook_events` deduplication table.

**Phase to address:** Credits + Stripe integration phase.

---

### Pitfall 6: Credit Balance Race Condition (Double-Spend Under Concurrent Requests)

**What goes wrong:**
User triggers two simulations simultaneously (or client retries a failed request). Both requests read the credit balance, both see sufficient credits, both deduct. User effectively runs two simulations for the price of one. At low traffic this is rare; it's exploitable at any scale.

**Why it happens:**
A read-then-write pattern without a lock: `SELECT balance FROM profiles WHERE id = $1`, then `UPDATE profiles SET balance = balance - 1`. Between the SELECT and UPDATE, another request can read the same balance.

**How to avoid:**
- Use PostgreSQL's `SELECT FOR UPDATE` to lock the row during the transaction, preventing concurrent reads of the same row until the transaction commits.
- Alternatively, use an atomic credit ledger pattern: INSERT a deduction row with a constraint that the running sum cannot go negative (enforced via a check or a Postgres function).
- Expose credit deduction as a Supabase RPC (Postgres function) that runs atomically inside the database rather than in application code.
- Example: `CALL deduct_credit(user_id, amount)` — the function checks and deducts in one transaction.

**Warning signs:**
- Credit deduction is implemented as two separate queries (SELECT balance, then UPDATE balance) without a transaction or lock.
- No database-level constraint preventing negative credit balance.

**Phase to address:** Credits + Stripe integration phase.

---

### Pitfall 7: Vercel Free Tier 10-Second Timeout Killing Simulation Status Polls

**What goes wrong:**
Next.js API routes on Vercel Hobby (free) tier have a 10-second execution limit. Any route that proxies to the Flask backend or waits for a response exceeding 10 seconds receives a 504 from Vercel — before Flask even responds. This breaks the simulation trigger endpoint if Flask takes >10s to acknowledge the job.

**Why it happens:**
MiroFish simulations are inherently long-running (minutes). Developers write a simple "trigger simulation and wait for result" API route. Works in local dev (no timeout). Fails silently in production.

**How to avoid:**
- Decouple trigger from result: the Next.js API route only submits the job to Flask and immediately returns a job ID (should complete in <1s). Flask acknowledges receipt, not completion.
- Track job status via polling against Supabase (Flask writes progress to the DB) or Supabase Realtime.
- Never proxy a long-running request through a Vercel function.
- For the Flask trigger endpoint: implement a "fire and forget" pattern — Flask receives the request, starts the simulation in a background thread, and returns `202 Accepted` with the job ID immediately.
- The 10s limit applies to Hobby tier; Pro tier gets 60s. Plan accordingly if upgrading.

**Warning signs:**
- Any Next.js API route that calls `fetch(MIROFISH_API_URL + '/simulate/...')` and awaits the full simulation result.
- Simulation triggers timing out in production but working in local dev.

**Phase to address:** Simulation integration + job orchestration phase.

---

### Pitfall 8: User LLM API Keys Stored Unencrypted (or Logged)

**What goes wrong:**
User-supplied OpenAI/Anthropic/Gemini API keys are stored in plain text in the Supabase `profiles` table. A database breach, a misconfigured RLS policy, or a nosy admin query exposes all user API keys. Users face financial exposure on their LLM accounts.

A secondary failure mode: API keys passed in request bodies or query params get logged in Vercel function logs or Supabase statement logs.

**Why it happens:**
Developers treat the API key as just another profile field. Encryption adds complexity and is deferred as "we'll add it later." It never gets added.

**How to avoid:**
- Use Supabase Vault for storing user secrets — it encrypts at rest using libsodium and manages key derivation internally. Do not use pgsodium directly (it is being deprecated as of 2025).
- Disable Supabase statement logging while inserting secrets into Vault to prevent keys from appearing in logs.
- Never pass API keys as URL query parameters — use request body or Authorization header only.
- On the Flask backend side: receive the key via HTTPS request body, use it in memory for the duration of the request, and never log it.
- In Next.js API routes: pass the decrypted key to Flask in the request body, not as a query string or in a URL that might be logged.
- Never store the raw key in the JWT or in a cookie.

**Warning signs:**
- LLM API key stored as a plain `text` column in the `profiles` table.
- API key visible in Supabase Studio table browser.
- API key appearing in Vercel function logs or network tab URL.

**Phase to address:** Auth + Database foundation phase (schema design), then Settings + LLM key management phase (UI).

---

### Pitfall 9: Flask CORS Misconfiguration in Production (Duplicate Headers via Nginx)

**What goes wrong:**
Flask uses `flask-cors` to set `Access-Control-Allow-Origin`. In production, Nginx is placed in front of Flask and also adds CORS headers. The browser receives duplicate `Access-Control-Allow-Origin` headers and rejects the response — simulations fail silently with a CORS error that doesn't appear in server logs.

A separate failure: Flask sets `Access-Control-Allow-Origin: *` while the Next.js app sends `credentials: 'include'` — the browser refuses this combination per the CORS spec.

**Why it happens:**
Flask CORS works in local dev. Nginx config is copied from a template that includes CORS headers. The duplication only surfaces in production with a real domain.

**How to avoid:**
- On the Hetzner Nginx config: do NOT add CORS headers. Let `flask-cors` handle them exclusively.
- Configure `flask-cors` with an explicit origin allowlist (`origins=["https://your-preflight-domain.com"]`) rather than `*`.
- Do not use `credentials: 'include'` in fetch calls to Flask; the API key auth header is sufficient and doesn't require credentials mode.
- The preferred Preflight pattern: Next.js API route calls Flask server-to-server (from Vercel function, not from browser). Browser calls Next.js API routes only. CORS between browser and Flask never needed.

**Warning signs:**
- Frontend JavaScript directly fetches `MIROFISH_API_URL` from the browser (not through a Next.js API route).
- `Access-Control-Allow-Origin` header appearing twice in response headers.

**Phase to address:** Simulation integration phase (architecture decision about browser-direct vs. server-proxy).

---

### Pitfall 10: Supabase Realtime Subscriptions Not Cleaned Up on Unmount

**What goes wrong:**
Supabase Realtime subscriptions opened in React components (e.g., to track simulation progress) are never unsubscribed. Every navigation away from the simulation status page opens a new WebSocket channel without closing the old one. After a few navigations, the user has dozens of open channels, causing: memory leaks, degraded Realtime performance for all users, and eventual WebSocket connection limits.

**Why it happens:**
The subscription is set up correctly but the `useEffect` cleanup return is missing or incomplete. Supabase does auto-close channels 30 seconds after disconnection, but doesn't handle in-page leaks.

**How to avoid:**
- Always return a cleanup function from `useEffect` that calls `supabase.removeChannel(channel)`.
- Pattern: `const channel = supabase.channel(...); return () => { supabase.removeChannel(channel); }`.
- Alternatively, for simulation status tracking, use polling (`setInterval` + `clearInterval` in cleanup) as the simpler, more predictable approach given simulations complete once and status tracking is finite.

**Warning signs:**
- `useEffect` with a Supabase subscription but no return cleanup function.
- Supabase dashboard shows far more Realtime connections than active users.

**Phase to address:** Simulation status tracking phase.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Store credit balance as a single integer column on `profiles` | Simple reads/writes | No audit trail, no way to reconcile disputes, race condition prone | Never — use a transactions ledger |
| Skip RLS on internal-only tables | Faster development | Any mis-scoped key exposes the table | Never in production |
| Direct browser-to-Flask calls (bypassing Next.js API routes) | Fewer hops, simpler | CORS complexity, API key exposed to browser, no server-side audit | Never — all Flask calls go server-to-server |
| Plain-text LLM API key storage | Trivially simple | User API key exposure on any DB leak | Never |
| Polling every 1 second for simulation status | Simple to implement | Supabase free tier rate limits, noisy logs | Only during early MVP; switch to longer interval or Realtime before launch |
| Single webhook endpoint without idempotency | Fast to build | Double-credits on Stripe retries | Never for payment flows |
| `getSession()` for server auth checks | One less network call | Spoofable by malicious cookies | Never in server-side auth checks |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Supabase Auth | Calling `getSession()` in middleware | Call `getUser()` — hits auth server, validates token |
| Supabase RLS | Testing policies in SQL editor (runs as superuser, bypasses RLS) | Test via SDK with a real authenticated test user |
| Supabase Vault | Using deprecated `pgsodium` directly | Use `vault.create_secret()` / `vault.read_secret()` API |
| Supabase Vault | Inserting secrets while statement logging is enabled | Disable statement logging before `vault.create_secret()` calls |
| Stripe Webhooks | Verifying signature using raw body after JSON.parse | Verify signature against raw body string before any parsing |
| Stripe Webhooks | Processing in the handler before returning 200 | Return 200 immediately, process asynchronously |
| Flask CORS | Adding CORS headers in both Nginx and flask-cors | Set CORS in one place only (flask-cors); Nginx passes through |
| Flask API Key | Sending the key as a query param in the URL | Send in request body or Authorization header only |
| Vercel Functions | Awaiting full simulation result in an API route | Fire-and-forget: Flask returns job ID, Next.js stores it, frontend polls |
| Supabase Realtime | Creating channel in `useEffect` without a cleanup return | Always `return () => supabase.removeChannel(channel)` |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| No index on `user_id` in RLS policies | Slow queries that pass RLS, full table scans | `CREATE INDEX ON simulations(user_id)` | ~1,000 rows |
| Polling simulation status every 1s | Supabase free tier connection/request limits hit, logs flooded | Poll every 3-5s or use Realtime | ~10 concurrent users |
| Supabase Storage for large creative uploads without size limits | Storage quota exhausted, slow uploads | Enforce file size limit (5MB max for images) on client + server | First viral user |
| LLM creative analysis call in the synchronous request path | Users wait 10-20s for wizard to load next step | Show immediate "analyzing..." state, stream or background the vision call | Always noticeable |
| Credit balance read + deduct without a transaction | Double-spend under concurrent requests | Use Postgres function (RPC) for atomic check-and-deduct | 2 simultaneous requests |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Exposing `SUPABASE_SERVICE_ROLE_KEY` to client | Bypasses all RLS, full DB access for anyone | Only use in Next.js API routes / Server Actions, never in client code or `NEXT_PUBLIC_` vars |
| Storing user LLM API keys in plain text | Key exposure on any DB breach or RLS misconfiguration | Use Supabase Vault for at-rest encryption |
| Logging LLM API keys in server logs | Keys in Vercel log drain or Supabase statement logs | Sanitize all request bodies before logging; disable statement logging during Vault operations |
| Flask API key auth using a weak or static key | Brute-forceable, no rotation | Generate a 256-bit random key, store in Hetzner env, rotate on compromise |
| Using `user_metadata` claims in RLS policies | Users can modify their own `user_metadata`, escalating privileges | Use only `auth.uid()` and `app_metadata` (set only server-side) in RLS policies |
| Accepting Stripe webhook without signature verification | Fake webhooks can grant free credits | Always verify `stripe.webhooks.constructEvent(rawBody, sig, secret)` |
| Passing simulation job credentials (LLM key) in Flask job payload stored in DB | Keys at rest in simulation job records | Decrypt key at time of job execution, never persist to job record |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| No progress indication during simulation (5-15 min job) | Users assume the app is broken, navigate away, re-trigger | Show stage-by-stage progress: "Building graph... Running simulation... Generating report..." |
| Showing "0 credits" error only after simulation starts | User waited for job submission, then hits a wall | Check credit balance before wizard completion, show a gate with purchase CTA |
| Credit deduction before simulation completes | User loses a credit on a backend error | Deduct credit only after Flask returns a successful job completion signal |
| Unclear "add your API key" onboarding for non-technical marketers | Users don't know what an API key is or where to get it | Step-by-step guide per provider (OpenAI, Anthropic, Gemini) with direct links to their API key pages |
| Showing raw MiroFish JSON/markdown report output | Confusing jargon, overwhelming for non-researchers | Always post-process through LLM to produce marketer-structured plain-English answers |
| No error state for failed simulations | User doesn't know whether to retry or contact support | Explicit "simulation failed" state with: reason, credit refund status, and retry button |

---

## "Looks Done But Isn't" Checklist

- [ ] **Supabase RLS:** Every table has RLS enabled AND policies created — verify by querying through an authenticated SDK client (not SQL editor)
- [ ] **Stripe idempotency:** Webhook handler checks for duplicate `stripe_event_id` before processing credits — verify by replaying the same webhook event twice and confirming balance increments only once
- [ ] **Credit deduction:** Deduction is atomic (Postgres RPC or `SELECT FOR UPDATE`) — verify by firing two simultaneous simulation requests and confirming only one succeeds
- [ ] **JWT security:** Auth checks use `getUser()` not `getSession()` in all API routes and middleware — grep for `getSession` in server-side files
- [ ] **No ISR on auth pages:** All authenticated pages have `export const dynamic = 'force-dynamic'` — verify by building and checking the `.next/server` output
- [ ] **Supabase Vault:** LLM API keys readable from DB only via `vault.read_secret()`, not visible in table browser — verify by opening Supabase Studio and confirming no plain-text key column
- [ ] **Realtime cleanup:** Every `useEffect` with a Supabase channel subscription returns a cleanup function — grep for `supabase.channel` without adjacent `removeChannel`
- [ ] **Vercel timeout:** No Next.js API route awaits Flask simulation completion synchronously — verify by checking all routes that call `MIROFISH_API_URL` return within 2 seconds
- [ ] **CORS architecture:** Browser never calls Flask directly — verify by checking no `MIROFISH_API_URL` appears in client-side React components
- [ ] **Webhook signature verification:** Stripe webhook uses raw body for signature, not parsed JSON — verify the raw body is passed to `stripe.webhooks.constructEvent`

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| RLS misconfiguration exposing user data | HIGH | Immediately enable RLS + add policies; audit access logs for unauthorized reads; notify affected users |
| Double-credited users from non-idempotent webhook | MEDIUM | Query `credit_transactions` for duplicates; run SQL to remove duplicate credits; add idempotency retroactively |
| Module-level Supabase client session leak | MEDIUM | Move client initialization inside handlers; force redeploy; users may need to re-login |
| User API keys in plain text discovered | HIGH | Rotate all stored keys (users must re-enter); migrate to Vault; audit logs for exposure |
| Vercel timeout on simulation trigger | LOW | Move to fire-and-forget pattern; no data loss, just a UX fix |
| Realtime subscription leak causing degraded service | LOW | Force-refresh clients; add cleanup to useEffect; Supabase will auto-close stale channels after 30s |
| Flask CORS duplicate headers blocking production | LOW | Remove CORS from Nginx config; redeploy Flask; no data loss |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| RLS tables without policies | Phase 1: Auth + DB foundation | Query via authenticated SDK client, confirm data visibility scoped per user |
| `getSession()` in server code | Phase 1: Auth + DB foundation | Grep all API routes for `getSession`; replace with `getUser` |
| Module-level Supabase client | Phase 1: Auth + DB foundation | Code review: no `createClient` at module scope in API routes |
| ISR cache JWT leak | Phase 1: Auth + DB foundation | Confirm `force-dynamic` on all authenticated routes |
| User LLM key unencrypted | Phase 1: Schema design + Phase 3: Settings UI | Vault read/write round-trip test; key not visible in Studio |
| Stripe non-idempotent webhook | Phase 2: Credits + Stripe | Replay webhook twice, verify balance increments once |
| Credit balance race condition | Phase 2: Credits + Stripe | Concurrent request test: 2 simultaneous deductions, 1 succeeds |
| Vercel 10s timeout | Phase 3: Simulation integration | Load test: trigger simulation from production, confirm 202 in <1s |
| Flask CORS production failure | Phase 3: Simulation integration | Cross-origin request from Vercel preview URL to Hetzner backend |
| Realtime subscription leak | Phase 3: Simulation status tracking | Open simulation page, navigate away 5x, confirm channel count stable |

---

## Sources

- [10 Common Mistakes Building with Next.js and Supabase](https://www.iloveblogs.blog/post/nextjs-supabase-common-mistakes)
- [Supabase RLS Docs](https://supabase.com/docs/guides/database/postgres/row-level-security)
- [Fixing RLS Misconfigurations in Supabase](https://prosperasoft.com/blog/database/supabase/supabase-rls-issues/)
- [Supabase RLS Performance and Best Practices](https://supabase.com/docs/guides/troubleshooting/rls-performance-and-best-practices-Z5Jjwv)
- [Setting up Server-Side Auth for Next.js — Supabase Docs](https://supabase.com/docs/guides/auth/server-side/nextjs)
- [Stripe Webhook Race Condition Guide](https://excessivecoding.com/blog/billing-webhook-race-condition-solution-guide)
- [Best Practices for Stripe Webhooks — Stigg](https://www.stigg.io/blog-posts/best-practices-i-wish-we-knew-when-integrating-stripe-webhooks)
- [The Race Condition You're Shipping With Stripe Webhooks](https://dev.to/belazy/the-race-condition-youre-probably-shipping-right-now-with-stripe-webhooks-mj4)
- [How to Solve Next.js Timeouts — Inngest](https://www.inngest.com/blog/how-to-solve-nextjs-timeouts)
- [Long-Running Background Functions on Vercel — Inngest](https://www.inngest.com/blog/vercel-long-running-background-functions)
- [Vercel Functions Limitations](https://vercel.com/docs/functions/limitations)
- [Supabase Vault Docs](https://supabase.com/docs/guides/database/vault)
- [Sensitive Data Encryption With Supabase](https://medium.com/@yogeshmulecraft/sensitive-data-encryption-with-supabase-77737d0871e8)
- [pgsodium Pending Deprecation — Supabase Docs](https://supabase.com/docs/guides/database/extensions/pgsodium)
- [Supabase Realtime Troubleshooting](https://supabase.com/docs/guides/realtime/troubleshooting)
- [Solving CORS Issues Between Next.js and Python Backend](https://medium.com/@nmlmadhusanka/solving-cors-issues-between-next-js-and-python-backend-93800a4ee633)
- [Background Jobs for Node.js using Next.js, Inngest, Supabase, and Vercel](https://medium.com/@cyri113/background-jobs-for-node-js-using-next-js-inngest-supabase-and-vercel-e5148d094e3f)
- [Vercel Pricing Breakdown 2025 — Flexprice](https://flexprice.io/blog/vercel-pricing-breakdown)

---

*Pitfalls research for: Next.js + Supabase + Stripe SaaS (Preflight) wrapping Flask simulation backend*
*Researched: 2026-03-24*
