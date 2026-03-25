# Roadmap: Preflight

## Overview

Preflight is a marketer-facing ad pre-testing SaaS that wraps the MiroFish simulation engine in a Next.js BFF (Backend-for-Frontend) layer. The build journey prioritizes getting the full simulation workflow running end-to-end locally before any billing or polish work. Auth and schema come first (everything depends on this), then the MiroFish backend extensions so the local instance at localhost:5001 can serve Preflight, then the three-step simulation workflow — creative upload, audience wizard and launch, report delivery — in a tight loop. Only after that core workflow is proven locally do we layer on onboarding polish and Stripe billing.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Auth & Foundation** - Next.js project scaffold, Supabase schema with RLS, email + Google OAuth, protected routes
- [ ] **Phase 2: MiroFish Backend** - API key auth on Flask endpoints, single-call pipeline endpoint, callback to Preflight (targets localhost:5001)
- [ ] **Phase 3: Creative Upload & Analysis** - Supabase Storage upload, LLM vision analysis, confirmation step
- [ ] **Phase 4: Simulation Wizard & Launch** - Audience builder wizard, seed doc, fire-and-forget launch, real-time status
- [ ] **Phase 5: Report & Polish** - LLM post-processing, structured report view, mobile responsive design
- [ ] **Phase 6: Settings & Onboarding** - LLM key setup with encryption, provider picker, profile, first-run walkthrough
- [ ] **Phase 7: Credits & Billing** - Stripe Checkout, idempotent webhook, credit balance, transaction history

## Phase Details

### Phase 1: Auth & Foundation
**Goal**: Users can securely access Preflight and the codebase is correctly scaffolded with a Supabase schema that enforces data isolation from day one
**Depends on**: Nothing (first phase)
**Requirements**: AUTH-01, AUTH-02, AUTH-03, AUTH-04, AUTH-05, INFR-01, INFR-02, INFR-03, INFR-06
**Success Criteria** (what must be TRUE):
  1. User can create an account with email and password and receive a confirmation email
  2. User can sign up and log in with Google OAuth in one click
  3. User session persists across browser refresh without re-prompting login
  4. User can request a password reset email and set a new password via the link
  5. Visiting any app route while logged out redirects to the login page; the landing page is publicly accessible
**Plans**: TBD
**UI hint**: yes

### Phase 2: MiroFish Backend
**Goal**: The local Flask instance at localhost:5001 is secured for Preflight access, exposes a single-call pipeline endpoint, and pushes status updates back to Preflight — all without touching existing functionality
**Depends on**: Phase 1
**Requirements**: MFBE-01, MFBE-02, MFBE-03, MFBE-04, MFBE-05
**Success Criteria** (what must be TRUE):
  1. A request to any Flask endpoint without a valid API key bearer token receives a 401 response
  2. A single POST to the pipeline endpoint with a seed document and user LLM key starts the full ontology → graph → simulation → report chain and returns a task_id immediately (202 Accepted)
  3. Flask sends a POST to the configured PREFLIGHT_CALLBACK_URL env var each time simulation status changes (e.g., building_graph, simulating, generating_report, complete, failed)
  4. All existing MiroFish API endpoints continue to work exactly as before for the Vue frontend and direct users
**Plans**: TBD

### Phase 3: Creative Upload & Analysis
**Goal**: Users can submit their creative — image, thumbnail, or copy — and receive an AI-generated structured analysis they confirm before continuing
**Depends on**: Phase 1
**Requirements**: CRTV-01, CRTV-02, CRTV-03, CRTV-04, CRTV-05
**Success Criteria** (what must be TRUE):
  1. User can drag-and-drop or file-pick an image and see it uploaded and displayed without errors; file goes to Supabase Storage
  2. User can upload a video thumbnail using the same file picker interface
  3. User can paste or type ad copy / script text as an alternative to file upload
  4. After upload, the LLM automatically analyzes the creative and returns a structured profile (tone, CTA, product category, hook strength) without any manual input
  5. User sees the analysis summary on screen and must confirm it before the wizard advances
**Plans**: TBD
**UI hint**: yes

### Phase 4: Simulation Wizard & Launch
**Goal**: Users can describe their audience, ask their questions, and launch a simulation against the local MiroFish instance that tracks progress in real time — status pushed via Supabase Realtime
**Depends on**: Phase 2, Phase 3
**Requirements**: AUDC-01, AUDC-02, AUDC-03, AUDC-04, SIMU-01, SIMU-02, SIMU-03, SIMU-04, SIMU-05, SIMU-06, SIMU-07, SCRN-01, SCRN-02
**Success Criteria** (what must be TRUE):
  1. User answers 3 conversational questions about their audience and optionally selects niche tags; the wizard synthesizes these into a persona JSON
  2. User selects a target platform (Instagram / TikTok / Facebook / YouTube / LinkedIn) before launching
  3. User types their questions for the simulation in plain text and submits; Preflight builds and sends the MiroFish seed document to localhost:5001
  4. User sees a status page with human-readable stage labels (Building graph... Simulating... Generating report...) that update live without manual refresh
  5. The simulation list (home screen) shows all past simulations as cards with thumbnail, platform, status badge, and date
**Plans**: TBD
**UI hint**: yes

### Phase 5: Report & Polish
**Goal**: Users receive a structured, plain-English report answering their questions — and the entire product is mobile-responsive so marketers can review results on their phones
**Depends on**: Phase 4
**Requirements**: REPT-01, REPT-02, REPT-03, REPT-04, REPT-05, REPT-06, REPT-07, SCRN-03, INFR-05
**Success Criteria** (what must be TRUE):
  1. Report page shows one section per user question answered in plain English (not raw simulation JSON)
  2. Report includes a top-3 actionable findings summary, a prioritized "What to fix" list, and a key message clarity diagnosis ("Will they get what you're selling?")
  3. Report includes a sentiment breakdown (positive / neutral / skeptical / negative) and 2-3 agent quote excerpts with simulated persona labels
  4. Report is saved permanently and accessible from the simulation list on any return visit
  5. All screens — simulation list, wizard, report, settings — are usable on a 390px mobile viewport without horizontal scroll or obscured controls
**Plans**: TBD
**UI hint**: yes

### Phase 6: Settings & Onboarding
**Goal**: The proven local workflow gains a polished first-run experience — LLM key configured, profile set, walkthrough seen — so new users can self-serve without instructions
**Depends on**: Phase 5
**Requirements**: ONBD-01, ONBD-02, ONBD-03, ONBD-04, ONBD-05, ONBD-06, INFR-04, SCRN-04
**Success Criteria** (what must be TRUE):
  1. A first-time user logging in sees a guided setup prompt asking them to choose an LLM provider and enter their API key
  2. User can click "Test connection" and receive instant feedback that their key is valid (or invalid) before saving
  3. User's LLM API key is never visible in plain text in the database; it is stored via Supabase Vault
  4. User can set their handle, industry, and default platform on the Settings screen
  5. A newly signed-up user sees 1 free simulation credit in their balance and encounters a first-run walkthrough on their first simulation attempt
**Plans**: TBD
**UI hint**: yes

### Phase 7: Credits & Billing
**Goal**: Users can purchase credits via Stripe and the credit system enforces gate-keeping — no double-spends, no double-grants
**Depends on**: Phase 6
**Requirements**: BILL-01, BILL-02, BILL-03, BILL-04, BILL-05
**Success Criteria** (what must be TRUE):
  1. User can purchase one of three credit bundles (5/$19, 20/$59, 100/$199) via Stripe Checkout and credits appear in their balance after payment
  2. Credit balance is visible in the navigation on every authenticated page
  3. User can view a full transaction history showing both purchases and simulation usage with dates
  4. Attempting to start a simulation with 0 credits shows a purchase prompt instead of launching
  5. Replaying a Stripe webhook event does not grant credits twice (idempotency enforced via event ID deduplication)
**Plans**: TBD
**UI hint**: yes

## Progress

**Execution Order:**
Phases execute in numeric order. Phases 2 and 3 depend only on Phase 1 and can be worked in parallel if desired.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Auth & Foundation | 0/TBD | Not started | - |
| 2. MiroFish Backend | 0/TBD | Not started | - |
| 3. Creative Upload & Analysis | 0/TBD | Not started | - |
| 4. Simulation Wizard & Launch | 0/TBD | Not started | - |
| 5. Report & Polish | 0/TBD | Not started | - |
| 6. Settings & Onboarding | 0/TBD | Not started | - |
| 7. Credits & Billing | 0/TBD | Not started | - |
