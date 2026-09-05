# Vasooli — AI Revenue Recovery Agent

**Razorpay Buildathon 2026 — Track 03: AI Revenue Recovery**

An agent that detects revenue at risk across payment failures, checkout abandonment, payment degradation, and overdue B2B receivables — diagnoses the root cause, decides the most cost-effective intervention through a bounded ROI optimizer, executes it via real channels, and logs a full audit trail of every decision.

---

## The Problem

Revenue loss rarely happens in one clean step — a payment degrades, a checkout gets abandoned, a subscription fails, or an invoice goes overdue. This project closes the loop from **detecting** the problem to **diagnosing** it, **choosing** the right intervention, and **recovering** the money — with measured results, compliant escalation, stopping rules, and a full audit trail.

Full write-up: [`docs/solution_overview.md`](docs/solution_overview.md)
Architecture rationale: [`docs/architecture_justification.md`](docs/architecture_justification.md)

---

## Key Features

**Detection**
- Real Razorpay Test Mode webhook (`payment.failed`)
- Checkout-abandonment sweep (idle-session detection)
- Overdue-invoice sweep
- Predictive payment-degradation detector — flags risk *before* a hard failure

**Diagnosis**
- Rule-based root-cause classification from Razorpay's real error taxonomy
- Gemini-assisted reasoning fallback for ambiguous/unmapped cases

**Decision**
- Bounded action set (no free-form agent choices)
- ROI optimizer: expected value = recovery probability × amount − real channel cost
- Stopping rules: max attempts, cooldown windows, opt-out, minimum-viable-recovery threshold, high-value escalation threshold
- Adaptive probability recalibration from real observed outcomes (Bayesian-style update)

**Execution**
- Real WhatsApp Cloud API sends (approved templates + Gemini-personalized variant)
- Real Gmail SMTP sends, fully Gemini-composed (including Hinglish)
- SMS channel interface-complete, mocked send (documented scope decision)
- Real Razorpay Payment Links generated per case

**Trust & Transparency**
- Customer-facing magic-link portal — plain-language explanation, real payment link, genuine opt-out
- Shadow mode — projects recovery before anything is sent or any money moves
- Full immutable audit trail per event: diagnosed → decided → attempted → outcome

**Access**
- Admin role — full dashboard, batch view, shadow mode, live-event injector
- Recovery Agent role — escalation queue with Gemini-written case briefings

---

## Tech Stack

Django + Django REST Framework · SQLite · Razorpay Python SDK (Test Mode) · Meta WhatsApp Cloud API · Gmail SMTP · Google Gemini API (`gemini-3.5-flash-lite` / `gemini-3.6-flash`) · Vanilla HTML/CSS/JS · Chart.js

---

## Project Structure

| App | Responsibility |
|---|---|
| `apps/events` | Detection — models, real webhook, seed/detector commands |
| `apps/diagnosis` | Root-cause classification (rule-based + Gemini fallback) |
| `apps/decisioning` | Bounded action set, ROI optimizer, stopping-rule guards, adaptive recalibration |
| `apps/execution` | Real channel adapters (WhatsApp, Email, mocked SMS) + executor |
| `apps/intelligence` | Gemini client, diagnosis reasoning, message composition, escalation briefing, degradation risk scoring, cost guard |
| `apps/audit` | Audit trail, dashboard, batch list, shadow mode, agent escalation queue |
| `apps/portal` | Customer-facing magic-link page, opt-out |
| `apps/accounts` | Auth, Admin / Recovery Agent roles |
| `apps/core` | Public home page |

---

## Setup

```bash
git clone https://github.com/<you>/revenue-recovery-agent.git
cd revenue-recovery-agent

python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt
copy .env.example .env         # Windows: copy | macOS/Linux: cp
```

Fill in `.env` with your own keys (see **Real Integrations Setup** below for where to get each one).

```bash
python manage.py migrate
python manage.py createsuperuser
```

---

## Seeding a Demo Batch

```bash
python manage.py seed_batch --count 200
python manage.py seed_edge_cases
python manage.py seed_degradation_signals --count 15
python manage.py detect_at_risk_events
python manage.py detect_degradation
python manage.py seed_rules
python manage.py run_pipeline
python manage.py run_execution
python manage.py simulate_recovery_outcomes
python manage.py recalibrate_rules
```

Then:
```bash
python manage.py runserver
```

- Public site: `http://127.0.0.1:8000/`
- Admin ops dashboard: `http://127.0.0.1:8000/dashboard/` (sign up as Admin)
- Recovery Agent queue: sign up as Recovery Agent
- Django admin: `http://127.0.0.1:8000/admin/`

---

## Real Integrations Setup

**Razorpay Test Mode** — [dashboard.razorpay.com](https://dashboard.razorpay.com) → Settings → API Keys (test mode). Webhook needs a public URL via [ngrok](https://ngrok.com) (`ngrok http 8000`) registered under Settings → Webhooks with the `payment.failed` event.

**WhatsApp Cloud API** — [developers.facebook.com/apps](https://developers.facebook.com/apps) → Create App → add WhatsApp product → API Setup page gives a temporary access token, phone number ID, and a test-recipient allowlist. Templates need approval via WhatsApp Manager.

**Email** — Gmail requires a 16-character **App Password** (myaccount.google.com/apppasswords), not your normal password.

**Gemini** — API key from [aistudio.google.com/apikey](https://aistudio.google.com/apikey).

---

## Research Notes

Channel costs used in the ROI optimizer (`myproject/intervention_costs.py`) are grounded in published rates, not guesses:
- WhatsApp utility template: ~₹0.145/message (Meta rate card, India)
- Transactional SMS: ~₹0.20/message (MSG91 published rate)
- Gemini API calls: ~₹0.02–0.08/call depending on model tier

Razorpay's own **Agent Studio** (razorpay.com/agent-studio) was reviewed as part of this project's design process — see `docs/solution_overview.md` for the comparison and what this project does differently.

---

## Deliberate Scope Decisions

- **SMS is mocked** (cost-logged, not actually sent) — avoided a paid-provider KYC flow mid-hackathon; the channel interface is real and ready to swap in.
- **Recovery-outcome confirmation is simulated** for seeded/demo data (`simulate_recovery_outcomes`) — stands in for a real `payment.captured` webhook, which can't be observed synchronously in a hackathon timeframe. Documented, not hidden.
- **No Celery/background scheduler** — stopping-rule guards are timestamp-based and scheduler-agnostic by design, so this is a drop-in addition later, not a redesign. Chosen for reliability over infra complexity in a 2-day build.

Full build log, including everything that broke and how it was fixed: [`BUGLOG.md`](BUGLOG.md)

---

## License

Built for the Razorpay Buildathon 2026. No license restrictions applied.