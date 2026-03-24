# Preflight

## What This Is

Preflight is a pre-launch ad and content simulation platform for marketers. Users upload their creative (image, video thumbnail, or ad copy), describe their target audience through a guided wizard, ask their questions — and Preflight runs a behavioral simulation via the MiroFish engine, returning a structured report predicting how their audience will react before they spend a dollar. Built for marketers, not researchers. No jargon, no setup, no code.

## Core Value

Marketers can simulate audience reactions to their creative before spending real money — upload, describe, ask, get answers in plain English.

## Requirements

### Validated

- ✓ MiroFish simulation engine (ontology → graph → simulation → report pipeline) — existing
- ✓ LLM client supporting any OpenAI-compatible endpoint — existing
- ✓ Knowledge graph storage via Zep Cloud — existing
- ✓ OASIS/CAMEL-AI multi-agent simulation framework — existing
- ✓ Report generation with ReACT agent pattern — existing

### Active

- [ ] Next.js frontend with 4 screens (Simulation List, New Simulation Wizard, Report View, Settings/Onboarding)
- [ ] Supabase Auth (email + Google OAuth)
- [ ] Supabase database for profiles, simulations, reports, credit transactions
- [ ] Supabase Storage for user-uploaded creatives
- [ ] LLM vision call to analyze creative into structured JSON profile
- [ ] Conversational audience builder wizard (3 questions + niche tag library → persona JSON)
- [ ] Seed document builder (combines creative JSON + audience JSON + platform context → MiroFish .md)
- [ ] Simplified MiroFish pipeline endpoint (ontology → graph → simulation → report in one call)
- [ ] API key authentication on MiroFish Flask endpoints for Preflight access
- [ ] LLM post-processing of MiroFish report into marketer-structured answers
- [ ] Stripe credits system (5/$19, 20/$59, 100/$199) with Checkout + webhooks
- [ ] Credit deduction per simulation
- [ ] User settings: LLM provider picker (OpenAI/Anthropic/Gemini), API key storage (encrypted), profile info
- [ ] Simulation status tracking via Supabase Realtime or polling
- [ ] Configurable backend URL (local dev → Hetzner production)
- [ ] AGPL-3.0 compliance (public repo, footer link, MiroFish attribution)
- [ ] Mobile responsive design

### Out of Scope

- Team/collaboration features — not needed for v1, solo user focus
- PDF export — complexity without clear demand
- Zapier/webhook integrations — premature, no user validation
- Agency sub-accounts — defer until agency segment validated
- Custom model training — out of scope for MVP
- Scheduling/publishing integration — Preflight is pre-launch only
- Video processing — thumbnail/still sufficient for simulation
- Real-time chat — not relevant to the product
- Replacing existing MiroFish Vue frontend — stays as-is for power users

## Context

**Brownfield project.** MiroFish is an existing multi-agent simulation engine with a Vue 3 frontend and Flask backend. Preflight is a new Next.js application living in `preflight/` within this repo, providing a marketer-friendly interface on top of MiroFish's capabilities.

**Architecture split:**
- `preflight/` — Next.js 14 (App Router) deployed on Vercel. Handles all Preflight-specific logic via API routes: auth, profiles, credits, Stripe webhooks, LLM calls for creative analysis and audience building.
- `backend/` — Existing Flask backend on Hetzner. Gets minimal additions: API key auth layer and a simplified pipeline endpoint. All heavy simulation work stays here.
- Frontend calls Flask over HTTPS with configurable `MIROFISH_API_URL` env var.

**Target users:**
- Primary: In-house marketing managers at DTC brands ($1M-$20M revenue), spending $500-$5K/mo on paid social
- Secondary: Boutique content marketing agencies (3-15 people) managing TikTok/Instagram
- Tertiary: Solo creators (100K-500K followers) running Spark Ads or paid promotion

**Monetization:** Credit-based, no subscription. Users bring their own LLM API key (cost $0 to Preflight per LLM call). Preflight charges credits for simulation compute time on Hetzner (~$0.05 cost, 97%+ margin).

**Infrastructure budget:** ~$8-12/month (Hetzner VPS + Supabase free tier + Vercel free tier).

**License:** AGPL-3.0 (inherited from MiroFish). Source must be public. Moat is UX simplicity, vertical focus, and marketer-specific output.

## Constraints

- **Tech stack (frontend):** Next.js 14 App Router, TypeScript — deployed on Vercel
- **Tech stack (backend):** Supabase (Auth, DB, Storage, Realtime), Stripe for payments
- **Tech stack (simulation):** Existing Flask + MiroFish pipeline on Hetzner — extend, don't rewrite
- **License:** AGPL-3.0 — all source code must be publicly available
- **LLM cost:** $0 to Preflight — all LLM calls use user's own API key
- **Infrastructure:** Vercel free tier (frontend), Hetzner CX32 $8.20/mo (MiroFish backend)
- **Existing code:** MiroFish Vue frontend and Flask API must remain functional and untouched for existing users

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Next.js API routes for Preflight logic, Flask gets minimal additions | TypeScript preference, first-class Supabase/Stripe SDKs, no third service to manage | — Pending |
| Credits over subscription | Marketers run campaigns in bursts; no churn problem; lower onboarding friction | — Pending |
| User brings own LLM key | Eliminates LLM cost for Preflight; already validated on mirofish.live | — Pending |
| Supabase for auth + DB + storage + realtime | Free tier sufficient for MVP; consolidates infrastructure; great DX | — Pending |
| Preflight lives in MiroFish repo | AGPL compliance easier; shared backend; single source of truth | — Pending |
| Configurable backend URL | Local dev with `localhost:5001`, production points to Hetzner | — Pending |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-24 after initialization*
