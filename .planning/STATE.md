# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-24)

**Core value:** Marketers can simulate audience reactions to their creative before spending real money
**Current focus:** Phase 1 — Auth & Foundation

## Current Position

Phase: 1 of 7 (Auth & Foundation)
Plan: 0 of TBD in current phase
Status: Ready to plan
Last activity: 2026-03-24 — Roadmap revised; phase order resequenced to deliver core local workflow before billing/onboarding polish

Progress: [░░░░░░░░░░] 0%

## Performance Metrics

**Velocity:**
- Total plans completed: 0
- Average duration: —
- Total execution time: 0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

**Recent Trend:**
- Last 5 plans: —
- Trend: —

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Roadmap v2]: Phase order resequenced — core workflow (Auth → MiroFish Backend → Creative Upload → Wizard & Launch → Report) comes before onboarding polish and billing. Billing/Stripe is now Phase 7, deferred until local workflow is proven end-to-end.
- [Roadmap v2]: Local MiroFish instance at localhost:5001 is the initial API target. MIROFISH_API_URL env var switches to Hetzner for prod. No deployment work until core flow works locally.
- [Roadmap v2]: SIMU-04 (credit deduction before launch) remains in Phase 4 in the requirements. Credit gating is not enforced until Phase 7 billing is built — Phase 4 success criteria reflects this by omitting the credit deduction criterion.
- [Roadmap v1]: REQUIREMENTS.md header said 50 requirements; actual count from requirements list is 54 — 54 used as authoritative count.
- [Roadmap v1]: Research flags Phase 5 (Simulation Launch, now Phase 4) and Supabase Vault (now Phase 6) as needing deeper research before planning.

### Pending Todos

None yet.

### Blockers/Concerns

- Flask `/api/run-pipeline` endpoint contract (payload shape, task ID format, error codes) must be read from `backend/app/api/` before planning Phase 2 (MiroFish Backend)
- Supabase Vault API current state (`vault.create_secret` / `vault.read_secret`) should be verified before planning Phase 6 (Settings & Onboarding) — pgsodium deprecation note in research

## Session Continuity

Last session: 2026-03-24
Stopped at: Roadmap revised (phase order resequenced), STATE.md and REQUIREMENTS.md traceability updated — ready to plan Phase 1
Resume file: None
