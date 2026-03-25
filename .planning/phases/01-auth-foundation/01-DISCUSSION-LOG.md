# Phase 1: Auth & Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-24
**Phase:** 01-auth-foundation
**Areas discussed:** Styling & design system, Auth UX, Schema scope, Landing page

---

## Styling & Design System

### CSS Framework

| Option | Description | Selected |
|--------|-------------|----------|
| Tailwind CSS (Recommended) | Utility-first, fast iteration, great Next.js integration | ✓ |
| CSS Modules | Scoped CSS per component, no framework dependency | |
| shadcn/ui + Tailwind | Tailwind plus copy-paste component library | |

**User's choice:** Tailwind CSS
**Notes:** None

### Visual Direction

| Option | Description | Selected |
|--------|-------------|----------|
| Clean & professional | White backgrounds, subtle grays, blue/indigo accents. Linear/Notion feel | |
| Bold & playful | Vibrant gradients, rounded shapes, warm colors. Canva/Loom feel | ✓ |
| Minimal & dark | Dark backgrounds, monochrome with accent. Raycast/Arc feel | |

**User's choice:** Bold & playful
**Notes:** None

### Theme Mode

| Option | Description | Selected |
|--------|-------------|----------|
| Light only (Recommended) | Simpler to build, most marketers expect light interfaces | |
| Dark only | Bold/unusual for marketer tool | |
| Both with toggle | More polished but doubles design work. System preference detection | ✓ |

**User's choice:** Both with toggle
**Notes:** None

### Typography

| Option | Description | Selected |
|--------|-------------|----------|
| You decide | Claude picks a modern, readable font pairing | |
| Inter / system font | Clean, professional, universally readable | |
| Something distinctive | Display/heading font with personality paired with body font | ✓ |

**User's choice:** Something distinctive
**Notes:** None

---

## Auth UX

### Login/Signup Forms

| Option | Description | Selected |
|--------|-------------|----------|
| Custom forms (Recommended) | Build own UI with Supabase JS client. Full design control | |
| Supabase Auth UI | @supabase/auth-ui-react drop-in component | |
| Custom + social buttons | Custom email form with prominent Google button | ✓ |

**User's choice:** Custom + social buttons
**Notes:** None

### Auth Layout

| Option | Description | Selected |
|--------|-------------|----------|
| Tabbed single page (Recommended) | One /login page with tabs for Sign In / Sign Up | ✓ |
| Separate pages | /login and /signup as distinct pages | |
| You decide | Claude picks based on design direction | |

**User's choice:** Tabbed single page
**Notes:** None

### Email Confirmation

| Option | Description | Selected |
|--------|-------------|----------|
| Confirm-then-access (Recommended) | Must click email link before using app | ✓ |
| Immediate access | Gets in right away, confirmation in background | |
| You decide | Claude picks best approach for marketers | |

**User's choice:** Confirm-then-access
**Notes:** None

---

## Schema Scope

### Table Scope

| Option | Description | Selected |
|--------|-------------|----------|
| All tables now (Recommended) | Profiles, simulations, reports, credits, transactions with RLS | |
| Auth tables only | Just profiles + auth config. Each phase creates its own | ✓ |
| Auth + simulation tables | Profiles + simulations + reports. Credits deferred | |

**User's choice:** Auth tables only
**Notes:** None

### Migration Strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Supabase CLI migrations (Recommended) | supabase migration new / db push. SQL in supabase/migrations/ | ✓ |
| Dashboard + seed file | Create in dashboard, keep seed.sql for reference | |
| You decide | Claude picks best strategy | |

**User's choice:** Supabase CLI migrations
**Notes:** None

---

## Landing Page

### Landing Page Content

| Option | Description | Selected |
|--------|-------------|----------|
| Minimal auth gate (Recommended) | Hero + tagline + value prop + login CTA | ✓ |
| Full marketing page | Features, how-it-works, pricing preview | |
| Just the login form | Bare login page with logo | |

**User's choice:** Minimal auth gate
**Notes:** None

### Post-Login Destination

| Option | Description | Selected |
|--------|-------------|----------|
| Dashboard / simulation list | Straight to main app with empty state | |
| Placeholder home | Simple authenticated page with branding + "Coming soon" | ✓ |
| You decide | Claude picks best post-login experience | |

**User's choice:** Placeholder home
**Notes:** None

---

## Claude's Discretion

- Font pairing selection (within "distinctive + readable" constraint)
- Color palette specifics (within "bold & playful, warm" direction)
- Dark mode color adjustments
- Next.js folder structure
- Supabase client initialization approach
- RLS policy implementation
- Password reset flow UX

## Deferred Ideas

None — discussion stayed within phase scope
