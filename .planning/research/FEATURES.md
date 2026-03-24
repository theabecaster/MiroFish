# Feature Research

**Domain:** Ad pre-testing and content simulation platform (marketer-facing SaaS)
**Researched:** 2026-03-24
**Confidence:** MEDIUM — Competitor UX scraped directly; billing patterns from industry analysis; some specifics inferred from adjacent tools where direct evidence was unavailable.

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete or untrustworthy.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Creative upload (image/video thumbnail/copy) | Every competitor offers upload as step 1 — without it there is nothing to test | LOW | Supabase Storage handles file hosting. LLM vision call analyzes content. Drag-and-drop or file picker. |
| Audience definition | Users will not trust results from an unknown or generic audience — every platform (Zappi, Neurons, PickFu, System1) requires audience scoping | MEDIUM | Conversational wizard reduces friction. Demographics + platform context (TikTok, Instagram, etc.) minimum viable inputs. |
| Simulation status tracking | Async jobs take minutes — users need feedback that something is happening, not a blank screen | LOW | Supabase Realtime or polling. Progress indicator with stage labels (Building graph... Running simulation... Generating report...). |
| Structured report with plain-English summary | Marketers are not researchers — they expect to read, not interpret. Zappi, System1, Neurons all lead with an AI summary section | MEDIUM | MiroFish report post-processed by LLM into marketer-structured sections. No raw JSON exposed. |
| Reaction/sentiment breakdown | Table stakes metric across all competitors — what did the simulated audience feel? | MEDIUM | Derived from simulation output. Positive / neutral / skeptical / negative framing in plain language. |
| Key message clarity score or diagnosis | Core diagnostic that Zappi, System1, Behavio all surface — does the ad land its message? | MEDIUM | Framed as "Will they get what you're selling?" section in report. |
| Simulation history / list view | Users run multiple simulations and need to return to past results. A product without history feels like a toy | LOW | Supabase table query. Simulation list page is the product home. |
| Credit balance display | Pay-per-use systems must always show remaining balance — users will be anxious about unknowingly spending | LOW | Show in nav or header. Deduct on simulation start, not completion. |
| Credit purchase flow | Without a way to buy credits, the product has no monetization path. Stripe Checkout is industry standard | LOW | Three tiers (5/$19, 20/$59, 100/$199). One-time purchase, no subscription commitment. |
| Email + OAuth sign-up | Marketers expect Google SSO as a baseline in 2026. Email-only is a friction point at sign-up | LOW | Supabase Auth supports both natively. |
| Mobile responsive design | DTC marketers review results on mobile; boutique agency account managers are often on phone | MEDIUM | Next.js with Tailwind. Mobile-first layout for report view especially. |
| Error messaging when simulation fails | Simulations can fail (LLM errors, backend timeout). Users need clear explanation, not a spinner that disappears | LOW | Distinguish: "Your LLM API key is invalid" vs "Simulation timed out — credits refunded" vs "Internal error." |
| LLM API key setup (user-provided keys) | The product is explicitly built on BYOK model — onboarding cannot complete without it. Users need guidance | LOW | Settings screen with provider picker, key input, and a test-connection button. Clear instructions per provider. |

---

### Differentiators (Competitive Advantage)

Features that set Preflight apart. Not required, but valuable if implemented well.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Conversational audience wizard (3 questions) | Competitors like Zappi and System1 use demographic checkboxes — tedious and research-y. Conversational input removes the "I don't know what to put here" problem for DTC marketers | MEDIUM | Three guided questions: Who buys this? What platform? What's the goal? Maps to internal persona JSON fed to MiroFish. Include niche tag library as optional autocomplete. |
| LLM vision-powered creative analysis | Most competitors require manual tagging or description. Auto-extracting tone, message, call to action, product category from the uploaded image removes a friction step and improves simulation quality | MEDIUM | OpenAI Vision API or equivalent. Returns structured JSON: format, product, tone, CTA, brand signals. Shown back to user for confirmation before simulation launches. |
| Platform-specific simulation context | Neurons, Behavio and Zappi treat platforms generically. Preflight simulates TikTok vs Instagram vs Meta Feed behavior differently — the same ad lands differently on each | HIGH | Requires platform context in seed document builder. TikTok agents have different scroll behavior and attention patterns than Meta Feed agents. Start with 2-3 platforms. |
| "What to fix" section in report | Most competitor reports show scores. Preflight's differentiator is concrete, prioritized recommendations — "Change your hook in the first 3 seconds" not "Attention score: 62" | MEDIUM | LLM post-processing of MiroFish output with instruction to produce ordered fix list. Low implementation cost, high perceived value. |
| Agent conversation excerpt in report | Showing 2-3 quoted synthetic agent reactions makes the simulation feel real and builds trust in the result. Competitors show numeric scores without evidence — this surfaces the "why" | LOW | Pull notable quotes from simulation JSONL output. Display in a "What they said" section with simulated persona label. |
| Credit auto-refund on failure | Industry norm is opaque refund policies. Automatic, immediate refund when simulation fails removes risk anxiety and differentiates on trust | LOW | Detect simulation failure state in backend, trigger credit restore in same transaction. Communicate to user in UI with message. |
| Simulation re-run from existing inputs | Once a user has defined audience + creative, they should be able to tweak and re-run without re-entering everything. Reduces friction for iteration workflows | LOW | Pre-fill wizard from previous simulation record. Show "Run again with same inputs" or "Edit and re-run" options on report view. |
| Benchmark phrasing in report ("above average for DTC brands") | System1's "Star Rating" framework works because users immediately understand relative performance. Abstract scores are confusing. Relative language ("strong hook for TikTok DTC") adds instant context | LOW | Hardcoded benchmark buckets in LLM post-processing prompt. No live database needed at MVP — use trained language cues. |

---

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem good but create problems at this stage.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| PDF / slide export | Marketers want to share with stakeholders | Adds significant frontend complexity (PDF rendering, fonts, layout) with no direct revenue benefit. Design-heavy. Competes with core UX priorities in early phases | Share-by-link. Generate a shareable public report URL that renders in browser. Stakeholders open the link — no PDF needed. |
| Real-time agent feed / live simulation streaming | "Watching" the simulation run feels exciting and transparent | Simulation takes 5-10 minutes. WebSocket plumbing for live streaming adds infrastructure complexity disproportionate to value. Most users will not stay on the page | Status stages with polling (Building graph... Simulating... Generating report...). Async email notification when complete is more useful than live feed. |
| Team / multi-user accounts | Agencies want team sharing | Adds role management, invite flows, permission systems, and billing split logic. Not validated for v1. One user per account is acceptable at launch | Build account as a foundation — don't block it, just don't build sharing. A "copy link" feature on reports covers immediate sharing needs. |
| A/B variant comparison | "Which of my two ads is better?" is a natural follow-up question | Running two simulations costs 2 credits. Simultaneous side-by-side comparison requires a separate UI paradigm, data model, and report format. Not the core workflow | Users can run two simulations separately and compare reports manually. Label them clearly. Side-by-side is a v2 feature. |
| Attention heatmaps | Neurons, Realeyes, Behavio all offer visual attention overlays — looks impressive | Requires a computer vision model (EyeQuant-style) or separate eye-tracking dataset. Not derivable from the text-based MiroFish simulation pipeline without a dedicated CV integration | The "What they noticed first" section in the report written in plain language delivers equivalent insight without the vision infrastructure. |
| Custom model / persona fine-tuning | Power users want to upload their own customer interview data to train personas | Significant ML infrastructure, storage, and processing complexity. BYOK model means variable quality with user-provided data | The niche tag library in the audience wizard covers 80% of persona customization needs. Offer a free-text "additional context" field as a safety valve. |
| Zapier / webhook integrations | Automation-focused marketers want to trigger simulations from their stack | Zero validated demand pre-launch. Every integration is a surface area to maintain | Launch a documented API endpoint. Savvy users can build their own integrations. Zapier partnership is a v2 conversation. |
| Scheduling / recurring simulations | "Run every time I update my creative" | Requires job queue infrastructure, scheduling logic, and notification plumbing on top of an already complex stack | Not a pre-testing use case. Preflight is pre-launch, not ongoing monitoring. Explicitly out of scope. |
| Subscription / monthly billing | Recurring revenue feels more stable | Burst usage pattern of campaign marketers means subscription creates churn (they pay for a month, run 2 simulations, cancel). Credits match the actual usage rhythm and lower onboarding commitment | Maintain credit-only model. Consider credit bundles with small bonus for larger purchases to drive volume commitment. |

---

## Feature Dependencies

```
[Auth / Profile]
    └──required by──> [Credit Balance Display]
    └──required by──> [Simulation History]
    └──required by──> [LLM API Key Setup]

[LLM API Key Setup]
    └──required by──> [Creative Analysis (vision call)]
    └──required by──> [Simulation Run]
    └──required by──> [Report Generation (LLM post-processing)]

[Creative Upload]
    └──required by──> [Creative Analysis (vision call)]
                           └──feeds──> [Audience Wizard]
                                           └──feeds──> [Simulation Run]
                                                           └──produces──> [Structured Report]

[Stripe Credits Purchase]
    └──required by──> [Simulation Run] (gate: must have >= 1 credit)

[Simulation Run]
    └──required by──> [Simulation Status Tracking]
    └──required by──> [Structured Report]
    └──required by──> [Agent Quote Excerpts]
    └──required by──> [Credit Deduction]
    └──required by──> [Credit Auto-Refund on Failure]

[Simulation History]
    └──enables──> [Re-run from Existing Inputs]

[Structured Report]
    └──enhances──> [Agent Quote Excerpts]
    └──enhances──> ["What to Fix" Section]
    └──enhances──> [Benchmark Phrasing]
```

### Dependency Notes

- **Auth requires first**: Nothing works without a user session. Auth gates every feature downstream.
- **LLM key setup blocks simulations**: The BYOK model means no simulation can run until a valid API key is stored. Onboarding must surface this before the user reaches the wizard.
- **Creative analysis feeds audience wizard**: The structured creative JSON (tone, product, CTA) pre-populates context in the wizard and improves persona matching quality.
- **Credits gate simulation start**: The system must check balance before launching the MiroFish pipeline to avoid orphaned compute jobs with no payment.
- **Simulation history enables re-run**: Re-run is a low-effort differentiator, but requires simulation records to be queryable. Build the data model correctly the first time.

---

## MVP Definition

### Launch With (v1)

Minimum viable product — enough to validate that marketers will pay for AI-simulated pre-testing.

- [x] Auth (email + Google OAuth) — no auth, no product
- [x] LLM API key setup with provider picker and test-connection — blocks all simulation
- [x] Creative upload (image, video thumbnail, ad copy text) — the input surface
- [x] LLM vision creative analysis with confirmation screen — removes manual tagging friction
- [x] Conversational audience wizard (3 questions + niche tag library) — core UX differentiator
- [x] Simulation run with status tracking (stages + polling) — the product doing its job
- [x] Structured report: summary, sentiment breakdown, key message diagnosis, "what to fix" — the deliverable
- [x] Agent quote excerpts in report — trust and "wow" moment
- [x] Simulation history list — return visits
- [x] Credit balance display + purchase flow (Stripe Checkout, 3 tiers) — monetization
- [x] Credit auto-refund on failure — removes risk anxiety at purchase
- [x] Mobile responsive layout — DTC marketer on phone
- [x] Error states with user-facing messages — polish that prevents churn

### Add After Validation (v1.x)

Features to add once the core workflow is validated and users are returning.

- [ ] Re-run from existing inputs — trigger: users ask "can I tweak and retry?"
- [ ] Platform-specific simulation context (TikTok vs Meta vs Instagram) — trigger: users complain results feel generic
- [ ] Shareable report URL (public link) — trigger: users ask how to share with their team or client
- [ ] Benchmark phrasing in report ("strong for DTC") — trigger: users ask "is this good?"
- [ ] Email notification when simulation completes — trigger: users close the tab and miss results

### Future Consideration (v2+)

Features to defer until product-market fit is established.

- [ ] A/B variant comparison (side-by-side report) — defer: two separate runs cover the need; UI paradigm shift
- [ ] Team accounts and sharing — defer: validate solo user segment first
- [ ] API endpoint for programmatic simulation — defer: no validated demand
- [ ] Enhanced audience niche library expansion — defer: validate wizard works before adding complexity
- [ ] Attention heatmap visualization — defer: requires CV model integration outside current pipeline

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Auth + profile setup | HIGH | LOW | P1 |
| LLM API key setup | HIGH | LOW | P1 |
| Creative upload | HIGH | LOW | P1 |
| Vision-based creative analysis | HIGH | MEDIUM | P1 |
| Conversational audience wizard | HIGH | MEDIUM | P1 |
| Simulation run + status tracking | HIGH | MEDIUM | P1 |
| Structured report (summary + sentiment + diagnosis) | HIGH | MEDIUM | P1 |
| "What to fix" recommendations section | HIGH | LOW | P1 |
| Agent quote excerpts in report | MEDIUM | LOW | P1 |
| Credit balance display | HIGH | LOW | P1 |
| Stripe credit purchase (3 tiers) | HIGH | LOW | P1 |
| Credit auto-refund on failure | MEDIUM | LOW | P1 |
| Simulation history list | HIGH | LOW | P1 |
| Mobile responsive design | MEDIUM | MEDIUM | P1 |
| Error states and messaging | MEDIUM | LOW | P1 |
| Re-run from existing inputs | MEDIUM | LOW | P2 |
| Platform-specific simulation context | HIGH | HIGH | P2 |
| Shareable report URL | MEDIUM | LOW | P2 |
| Benchmark phrasing in report | MEDIUM | LOW | P2 |
| Email notifications on completion | MEDIUM | LOW | P2 |
| A/B variant side-by-side comparison | MEDIUM | HIGH | P3 |
| Team accounts and sharing | LOW | HIGH | P3 |
| Programmatic API endpoint | LOW | LOW | P3 |
| Attention heatmap visualization | LOW | HIGH | P3 |

---

## Competitor Feature Analysis

| Feature | Neurons AI | System1 / Test Your Ad | Zappi | PickFu / Ask Rally | Preflight Approach |
|---------|-----------|----------------------|-------|-------------------|-------------------|
| Creative upload | Image + video | Any ad format | TV, social, digital | Images, copy, mockups | Image, thumbnail, copy |
| Audience definition | Industry benchmarks + custom demographics | Custom sample targeting | Category-relevant panel (400 respondents) | 90+ demographic traits, 15M panel | Conversational wizard → persona JSON |
| Speed | "Seconds" (AI-only) | 3-7 days (human panel) | Hours to days (human survey) | Minutes to hours (panel) | 5-15 min (AI simulation) |
| Report output | Attention heatmap + engagement score | Star/Spike/Fluency + FaceTrace emotional curve | AI Quick Report + benchmark scores | AI summary + sentiment breakdown | Plain-English sections + agent quotes + fix list |
| Onboarding model | Enterprise sales / self-serve | Enterprise / self-serve with 2-week trial | Enterprise/agency focus | Self-serve, poll-by-poll | Self-serve, BYOK, credit purchase |
| Billing model | Subscription (enterprise) | Per-test or subscription | Subscription (enterprise) | Per-poll ($15+) or subscription | Credits, no subscription |
| Human panel data | Yes (neuroscience dataset) | Yes (real consumer survey) | Yes (survey panel) | Yes (15M respondents) | No — AI simulation only |
| Transparency of methodology | "95% accuracy" claim | Proprietary framework | Validated against market outcomes | Quantitative + qualitative | Show agent quotes to evidence the "why" |
| Target user | Enterprise brand teams | Mid-to-large brand teams | Enterprise insights teams | SMBs, DTC brands, agencies | DTC marketers, boutique agencies, solo creators |

**Key positioning insight (MEDIUM confidence):** Preflight sits in a gap between enterprise tools (Zappi, Neurons, System1) that require procurement and setup, and real-panel tools (PickFu) that are slow and expensive per test. Preflight's advantage is: instant AI simulation at low cost, marketer-grade UX (no research jargon), and honest plain-English output. The absence of a human panel is a weakness to address in copy ("behavioral simulation" framing, not "survey results").

---

## Sources

- [Behavio Labs — Ad testing software: what it is, how it works](https://www.behaviolabs.com/blog/ad-testing-software-what-it-is-how-it-works-the-best-platforms-in-2026)
- [Sovran — The 12 Best Creative Testing Software Tools](https://sovran.ai/blog/creative-testing-software)
- [Neurons AI — Ad Testing Metrics](https://www.neuronsinc.com/ad-testing/metrics)
- [Neurons AI — Neurons AI Platform](https://www.neuronsinc.com/neurons-ai)
- [System1 — Test Your Ad Platform](https://system1group.com/test-your-ad)
- [Zappi — What to look for in an ad testing platform](https://www.zappi.io/web/blog/what-to-look-for-in-ad-testing-platform/)
- [Zappi — Digital Ad Testing](https://www.zappi.io/web/creative-digital/)
- [PickFu — Products and Features](https://www.pickfu.com/products)
- [Ask Rally — Audience Simulator with AI Personas](https://askrally.com/)
- [AdSkate — Synthetic Audiences Guide 2025](https://www.adskate.com/blogs/synthetic-audiences-guide)
- [GetMonetizely — How to Structure SaaS Pricing for a Credit-Based Model](https://www.getmonetizely.com/articles/how-should-you-structure-saas-pricing-for-a-credit-based-model)
- [Growth Unhinged — What actually works in SaaS pricing right now (2025)](https://www.growthunhinged.com/p/2025-state-of-saas-pricing-changes)
- [Superads — The 6 Best Ad Testing Tools for Top Ad Performance](https://www.superads.ai/blog/best-ad-testing-tools)
- [Cometly — 9 Best AI Creative Testing Platforms](https://www.cometly.com/post/ai-creative-testing-platform)

---
*Feature research for: Preflight — marketer-facing ad pre-testing simulation platform*
*Researched: 2026-03-24*
