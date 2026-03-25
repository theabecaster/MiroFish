# Requirements: Preflight

**Defined:** 2026-03-24
**Core Value:** Marketers can simulate audience reactions to their creative before spending real money

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Authentication

- [ ] **AUTH-01**: User can sign up with email and password
- [ ] **AUTH-02**: User can sign up / log in with Google OAuth
- [ ] **AUTH-03**: User session persists across browser refresh
- [ ] **AUTH-04**: User can reset password via email link
- [ ] **AUTH-05**: All app routes except landing page require authentication

### Onboarding

- [ ] **ONBD-01**: User is prompted to set up LLM API key on first login (provider picker: OpenAI / Anthropic / Gemini)
- [ ] **ONBD-02**: User can test their LLM API key connection before saving
- [ ] **ONBD-03**: LLM API key is encrypted before storage in Supabase
- [ ] **ONBD-04**: User can set profile basics (handle, industry, default platform)
- [ ] **ONBD-05**: User receives 1 free simulation credit on signup
- [ ] **ONBD-06**: User sees guided first-run walkthrough for their first simulation

### Creative Upload & Analysis

- [ ] **CRTV-01**: User can upload image (drag-and-drop or file picker) stored in Supabase Storage
- [ ] **CRTV-02**: User can upload video thumbnail stored in Supabase Storage
- [ ] **CRTV-03**: User can paste ad copy / script as text input
- [ ] **CRTV-04**: LLM vision model auto-analyzes uploaded creative into structured JSON (tone, CTA, product category, hook strength)
- [ ] **CRTV-05**: User sees creative analysis summary before proceeding (confirmation step)

### Audience Builder

- [ ] **AUDC-01**: User answers 3 guided questions about their target audience via conversational wizard
- [ ] **AUDC-02**: User can select from pre-built niche tag library (DTC, finance, creator, B2B, health, etc.)
- [ ] **AUDC-03**: LLM synthesizes answers + tags into structured audience persona JSON
- [ ] **AUDC-04**: User selects target platform (Instagram / TikTok / Facebook / YouTube / LinkedIn)

### Simulation

- [ ] **SIMU-01**: User enters free-text questions ("What do you want to know about this creative?")
- [ ] **SIMU-02**: Preflight backend builds MiroFish seed document from creative JSON + audience JSON + platform + questions
- [ ] **SIMU-03**: Preflight backend calls MiroFish pipeline endpoint (single POST, returns task_id)
- [ ] **SIMU-04**: Preflight deducts 1 credit before launching simulation
- [ ] **SIMU-05**: User sees simulation status with stage labels (Building graph... Simulating... Generating report...)
- [ ] **SIMU-06**: MiroFish Flask calls Preflight callback URL on status changes
- [ ] **SIMU-07**: Preflight backend updates Supabase simulation record on each callback

### Report

- [ ] **REPT-01**: LLM post-processes MiroFish raw report into marketer-structured answers (one section per user question)
- [ ] **REPT-02**: Report includes plain-English summary with top 3 actionable findings
- [ ] **REPT-03**: Report includes "What to fix" prioritized recommendations list
- [ ] **REPT-04**: Report includes 2-3 agent quote excerpts with simulated persona labels
- [ ] **REPT-05**: Report includes sentiment breakdown (positive / neutral / skeptical / negative)
- [ ] **REPT-06**: Report includes key message clarity diagnosis ("Will they get what you're selling?")
- [ ] **REPT-07**: Report is saved permanently in Supabase

### Billing & Credits

- [ ] **BILL-01**: User can purchase credits via Stripe Checkout (5/$19, 20/$59, 100/$199)
- [ ] **BILL-02**: Stripe webhook grants credits with idempotency (deduplication table)
- [ ] **BILL-03**: User sees credit balance in navigation at all times
- [ ] **BILL-04**: User can view transaction history (purchases and usage)
- [ ] **BILL-05**: User cannot start simulation with 0 credits (blocked with purchase prompt)

### MiroFish Backend

- [ ] **MFBE-01**: Flask endpoints require API key bearer token authentication (for Preflight access)
- [ ] **MFBE-02**: New pipeline endpoint: single POST chains ontology -> graph -> simulation -> report, returns task_id immediately
- [ ] **MFBE-03**: Pipeline endpoint accepts user's LLM API key and provider in request body
- [ ] **MFBE-04**: Flask calls Preflight callback URL (PREFLIGHT_CALLBACK_URL env var) on simulation status changes
- [ ] **MFBE-05**: Existing MiroFish API endpoints remain functional and unchanged

### Infrastructure & Security

- [ ] **INFR-01**: Next.js project with configurable MIROFISH_API_URL env var (localhost for dev, Hetzner for prod)
- [ ] **INFR-02**: All MiroFish API calls go through Next.js API routes (browser never calls Flask directly)
- [ ] **INFR-03**: Supabase RLS policies on all tables (user can only access own data)
- [ ] **INFR-04**: LLM API keys encrypted at rest via Supabase Vault
- [ ] **INFR-05**: Mobile responsive design across all screens
- [ ] **INFR-06**: AGPL-3.0 license, public repo, footer link to GitHub + MiroFish attribution

### Screens

- [ ] **SCRN-01**: Simulation List (home) — cards with thumbnail, name, platform, status badge, date
- [ ] **SCRN-02**: New Simulation Wizard — 4-step flow with progress indicators
- [ ] **SCRN-03**: Simulation Report — header + question sections + summary + recommendations
- [ ] **SCRN-04**: Settings — LLM key setup, profile, billing/credits, transaction history

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Enhanced Simulation

- **ESIM-01**: Re-run simulation from existing inputs (pre-fill wizard from previous sim)
- **ESIM-02**: Platform-specific simulation context (TikTok vs Meta vs Instagram behavior differences)
- **ESIM-03**: Benchmark phrasing in report ("strong for DTC", "above average for TikTok")

### Sharing & Collaboration

- **SHAR-01**: Shareable public report URL (no auth required to view)
- **SHAR-02**: Email notification when simulation completes

### Billing Expansion

- **BEXP-01**: Tiered credit costs based on simulation depth
- **BEXP-02**: Credit auto-refund on simulation failure

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Team / multi-user accounts | Not validated for v1; one user per account acceptable at launch |
| PDF / slide export | High frontend complexity, low revenue impact; share-by-link covers the need |
| A/B variant comparison | Users can run two sims and compare manually; UI paradigm shift not justified |
| Attention heatmaps | Requires CV model not derivable from MiroFish text-based simulation |
| Custom model / persona training | Significant ML infrastructure; niche tag library covers 80% of need |
| Zapier / webhook integrations | Zero validated demand; documented API endpoint for power users |
| Scheduling / recurring sims | Preflight is pre-launch, not monitoring; out of scope by design |
| Subscription billing | Credits match burst usage pattern; subscriptions create churn |
| Real-time agent streaming feed | 5-10 min sim time; status stages with polling sufficient |
| Video processing | Thumbnail/still sufficient for simulation purposes |
| Flask connects to Supabase | Only Preflight backend talks to Supabase; Flask uses callback URL |

## Traceability

Which phases cover which requirements. Updated during roadmap revision 2026-03-24.

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUTH-01 | Phase 1 | Pending |
| AUTH-02 | Phase 1 | Pending |
| AUTH-03 | Phase 1 | Pending |
| AUTH-04 | Phase 1 | Pending |
| AUTH-05 | Phase 1 | Pending |
| ONBD-01 | Phase 6 | Pending |
| ONBD-02 | Phase 6 | Pending |
| ONBD-03 | Phase 6 | Pending |
| ONBD-04 | Phase 6 | Pending |
| ONBD-05 | Phase 6 | Pending |
| ONBD-06 | Phase 6 | Pending |
| CRTV-01 | Phase 3 | Pending |
| CRTV-02 | Phase 3 | Pending |
| CRTV-03 | Phase 3 | Pending |
| CRTV-04 | Phase 3 | Pending |
| CRTV-05 | Phase 3 | Pending |
| AUDC-01 | Phase 4 | Pending |
| AUDC-02 | Phase 4 | Pending |
| AUDC-03 | Phase 4 | Pending |
| AUDC-04 | Phase 4 | Pending |
| SIMU-01 | Phase 4 | Pending |
| SIMU-02 | Phase 4 | Pending |
| SIMU-03 | Phase 4 | Pending |
| SIMU-04 | Phase 4 | Pending |
| SIMU-05 | Phase 4 | Pending |
| SIMU-06 | Phase 4 | Pending |
| SIMU-07 | Phase 4 | Pending |
| REPT-01 | Phase 5 | Pending |
| REPT-02 | Phase 5 | Pending |
| REPT-03 | Phase 5 | Pending |
| REPT-04 | Phase 5 | Pending |
| REPT-05 | Phase 5 | Pending |
| REPT-06 | Phase 5 | Pending |
| REPT-07 | Phase 5 | Pending |
| BILL-01 | Phase 7 | Pending |
| BILL-02 | Phase 7 | Pending |
| BILL-03 | Phase 7 | Pending |
| BILL-04 | Phase 7 | Pending |
| BILL-05 | Phase 7 | Pending |
| MFBE-01 | Phase 2 | Pending |
| MFBE-02 | Phase 2 | Pending |
| MFBE-03 | Phase 2 | Pending |
| MFBE-04 | Phase 2 | Pending |
| MFBE-05 | Phase 2 | Pending |
| INFR-01 | Phase 1 | Pending |
| INFR-02 | Phase 1 | Pending |
| INFR-03 | Phase 1 | Pending |
| INFR-04 | Phase 6 | Pending |
| INFR-05 | Phase 5 | Pending |
| INFR-06 | Phase 1 | Pending |
| SCRN-01 | Phase 4 | Pending |
| SCRN-02 | Phase 4 | Pending |
| SCRN-03 | Phase 5 | Pending |
| SCRN-04 | Phase 6 | Pending |

**Coverage:**
- v1 requirements: 54 total
- Mapped to phases: 54
- Unmapped: 0

---
*Requirements defined: 2026-03-24*
*Last updated: 2026-03-24 — phase order revised to prioritize local end-to-end workflow before billing/onboarding polish*
