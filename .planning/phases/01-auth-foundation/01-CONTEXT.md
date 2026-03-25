# Phase 1: Auth & Foundation - Context

**Gathered:** 2026-03-24
**Status:** Ready for planning

<domain>
## Phase Boundary

Next.js 15 project scaffold for the Preflight app (separate repo), Supabase auth with email + Google OAuth, auth-related database schema with RLS policies, protected routing, and a public landing page. This phase delivers the foundation that all downstream phases build on.

</domain>

<decisions>
## Implementation Decisions

### Styling & Design System
- **D-01:** Use Tailwind CSS for styling (utility-first, fast iteration, great Next.js integration)
- **D-02:** Visual direction is bold & playful — vibrant gradients, rounded shapes, warm colors. Think Canva/Loom, not Linear/Vercel. Targeting marketers, not developers
- **D-03:** Support both light and dark mode with a toggle. Include system preference detection
- **D-04:** Use a distinctive heading font with personality (e.g., Plus Jakarta Sans, DM Sans, Space Grotesk) paired with a readable body font

### Auth UX
- **D-05:** Custom login/signup forms with a prominent "Continue with Google" button. Supabase JS client handles auth behind the scenes — no @supabase/auth-ui-react
- **D-06:** Single /login page with tabs to switch between Sign In and Sign Up
- **D-07:** Email confirmation required before access (confirm-then-access). User must click email link before using the app

### Schema Scope
- **D-08:** Phase 1 creates auth-related tables only (profiles). Each subsequent phase creates its own tables when needed
- **D-09:** Use Supabase CLI migrations (`supabase migration new` / `supabase db push`). SQL files version-controlled in `supabase/migrations/`

### Landing Page
- **D-10:** Minimal auth gate — hero with tagline, value prop, and login/signup CTA. Not a full marketing page. Full marketing site deferred
- **D-11:** After login, user sees a placeholder home page with Preflight branding and a "Coming soon" message. Phases 3-4 replace this with the real simulation list UI

### Claude's Discretion
- Font pairing selection within the "distinctive + readable" constraint (D-04)
- Color palette specifics within the "bold & playful, warm colors" direction (D-02)
- Dark mode color adjustments
- Next.js folder structure and routing patterns
- Supabase client initialization approach (SSR vs client-side)
- RLS policy implementation details
- Password reset flow UX details

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — AUTH-01 through AUTH-05 (authentication requirements), INFR-01 (configurable MIROFISH_API_URL), INFR-02 (API calls through Next.js routes), INFR-03 (Supabase RLS), INFR-06 (AGPL-3.0 license)

### Project Context
- `.planning/PROJECT.md` — Constraints section (tech stack, license, infrastructure), Context section (two-repo architecture, data flow rule)
- `.planning/ROADMAP.md` — Phase 1 details, success criteria, dependency graph

### Codebase Context
- `.planning/codebase/STACK.md` — Current MiroFish stack for reference (Preflight is separate but should understand what it calls)
- `.planning/codebase/ARCHITECTURE.md` — MiroFish architecture for understanding the API surface Preflight will eventually call

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None directly reusable — Preflight is a new Next.js project in a separate repo. MiroFish is Vue 3 + Flask

### Established Patterns
- MiroFish uses plain CSS with monospace font family — Preflight deliberately diverges with Tailwind and a bold/playful aesthetic
- MiroFish backend runs on Flask at port 5001 — Preflight will call this via MIROFISH_API_URL env var (Phase 2+)

### Integration Points
- Preflight repo (`github.com/theabecaster/preflight`) — does not exist yet, will be created
- Supabase project — needs to be created or configured
- MIROFISH_API_URL env var — configured in Phase 1, used starting Phase 2

</code_context>

<specifics>
## Specific Ideas

- Bold & playful visual direction inspired by Canva/Loom — warm, vibrant, approachable for marketers
- Distinctive heading typography to differentiate from typical developer-tool aesthetics

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-auth-foundation*
*Context gathered: 2026-03-24*
