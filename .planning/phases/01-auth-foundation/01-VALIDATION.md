---
phase: 1
slug: auth-foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-24
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | vitest (Next.js 15 + TypeScript) |
| **Config file** | `vitest.config.ts` (Wave 0 installs) |
| **Quick run command** | `npx vitest run --reporter=verbose` |
| **Full suite command** | `npx vitest run` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `npx vitest run --reporter=verbose`
- **After every plan wave:** Run `npx vitest run`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | INFR-01, INFR-06 | integration | `npx vitest run` | ❌ W0 | ⬜ pending |
| 01-02-01 | 02 | 1 | AUTH-01, AUTH-02 | unit | `npx vitest run` | ❌ W0 | ⬜ pending |
| 01-02-02 | 02 | 1 | AUTH-03, AUTH-04 | unit | `npx vitest run` | ❌ W0 | ⬜ pending |
| 01-03-01 | 03 | 1 | INFR-02, INFR-03 | unit | `npx vitest run` | ❌ W0 | ⬜ pending |
| 01-04-01 | 04 | 2 | AUTH-05 | integration | `npx vitest run` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `vitest` + `@testing-library/react` — install test framework
- [ ] `vitest.config.ts` — test configuration
- [ ] `tests/setup.ts` — shared test setup (mock Supabase client)

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Email confirmation delivery | AUTH-01 | Requires real email service | Create account, check inbox, click confirmation link |
| Google OAuth redirect flow | AUTH-02 | Requires Google OAuth credentials | Click "Continue with Google", complete OAuth flow |
| Password reset email delivery | AUTH-04 | Requires real email service | Request reset, check inbox, click link, set new password |
| Session persistence across refresh | AUTH-03 | Browser behavior | Log in, refresh page, verify still logged in |

*If none: "All phase behaviors have automated verification."*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
