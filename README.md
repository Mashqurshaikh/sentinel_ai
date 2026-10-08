# Sentinel AI

**An autonomous, privacy-preserving gateway for Shadow AI threat detection.**

Employees paste source code, customer data, and credentials into public AI
tools every day, usually without meaning to. Sentinel sits between an
employee and any external LLM: it scans the prompt (or an uploaded file),
scores the risk, masks anything sensitive, logs the result, and either
lets it through, flags it for review, or blocks it outright - and for
anything that isn't blocked, it can forward the sanitized prompt straight
to Claude, ChatGPT, or Gemini and hand back the real response, so there's
no manual copy/paste into a separate chat window.

This repo has four parts:
- a **FastAPI backend** that does the detection, scoring, auth, and LLM forwarding
- a **React dashboard** (light theme) for employees to scan prompts and
  admins to manage policy, approvals, and reports
- **login-backed identity** - every scan is tied to a real logged-in user,
  not a free-text field
- four **autonomous agents** that watch traffic, tune detection rules,
  brief admins, and retrain the model — all callable from the dashboard

---

## Getting a real AI response back

Set whichever provider key(s) you have before starting the backend:

```bash
export ANTHROPIC_API_KEY=sk-ant-...   # Claude
export OPENAI_API_KEY=sk-...          # ChatGPT
export GOOGLE_API_KEY=...             # Gemini
```

Then in the Gateway, pick a provider under "send response through" before
scanning. Low/medium-risk prompts get forwarded immediately after
sanitization; high-risk ones go to the approval queue first, and an admin
can choose a provider when approving. No keys set → the provider buttons
show "(no key)" and stay disabled, so nobody can pick an option that will
just error out.

## Logging in

First run seeds a default admin account: **admin / admin123** - change
this immediately if this ever runs anywhere but your own laptop.
Employees can self-register from the login screen; new accounts are
always created as "employee" role. Only an existing admin can promote
someone (there's no self-service path to admin, on purpose).

Once logged in, the Gateway uses your real username and department
automatically - no more typing in a name by hand.

---

## What it detects

| Category | How |
|---|---|
| API keys & credentials | Regex signatures for AWS, GitHub, Slack, Stripe, OpenAI/Anthropic keys, JWTs, DB connection strings, plus any custom rules you add |
| Personal data (PII) | spaCy NER (multi-word person names only - see note below) + regex for phone numbers, account numbers, emails, Aadhaar/PAN IDs, IPs |
| Source code | Heuristics for function/class definitions, SQL, common language keywords |
| Prompt injection | Pattern matching against known jailbreak/instruction-override phrasing |
| Compliance exposure | Every match above is tagged against GDPR, PCI-DSS, SOC 2, ISO 27001, India's DPDP Act, etc. |
| Chunked/incremental leaks | If a user has 3+ flagged messages within 30 minutes, later messages get escalated even if individually mild - catches someone splitting a leak across several prompts |

A TF-IDF + Logistic Regression classifier runs alongside the rule-based
detectors as a second opinion, catching paraphrased or novel risky prompts
the regex rules would miss - but only escalates the final risk level when
its own confidence is reasonably high, so an uncertain guess on an
everyday question can't override a clean rule-based verdict.

> **Note on PII detection:** only multi-word spaCy PERSON matches count
> (e.g. "Rahul Sharma"), and organizations/locations are deliberately
> **not** flagged. Small NER models misclassify unfamiliar place and brand
> names constantly ("what's the capital of France" would otherwise flag
> "France" as personal data), so this trade-off favors fewer false alarms
> on ordinary questions over catching every possible name variant.

## Features

- **Live scanning** — paste a prompt or upload a `.txt`/`.pdf`/`.docx` file, see
  it get analyzed with an animated scan, get back a sanitized version
- **Real LLM responses** — forward the sanitized prompt to Claude, ChatGPT,
  or Gemini and see the actual answer, not just a cleaned-up prompt to
  copy elsewhere
- **Login-backed accounts** — employee/admin roles, JWT sessions, admin-only
  pages actually enforced server-side, not just hidden in the UI
- **Real-time admin dashboard** — WebSocket-driven live feed, activity charts,
  department breakdown, one-click agent triggers
- **Admin approval queue** — blocked requests go into a real review queue;
  an admin can approve (optionally forwarding to an LLM) or reject, with the
  decision and reviewer recorded
- **Chunked-leak detection** — flags users sending repeated sensitive
  messages in a short window, even if each individual message looks mild
- **Custom policy rules** — add your own regex detection rules from the UI,
  no code changes needed
- **Compliance reporting** — regulatory tag breakdown, full CSV export of the
  audit trail
- **Four autonomous agents** — traffic monitoring, policy learning, threat
  intelligence reports, and model retraining, each triggerable via API or
  dashboard button

---

## Project layout

```
sentinel_v2/
├── data/
│   ├── generate_prompts.py       synthetic labelled prompt dataset
│   └── prompts.csv                generated in Step 3
├── detectors/
│   ├── secret_scanner.py           credential/API key regex rules
│   ├── pii_detector.py              spaCy NER + regex PII detection
│   ├── code_and_injection_detector.py   source code + injection heuristics
│   ├── compliance.py                 entity type -> regulation tag mapping
│   ├── file_extractor.py              pulls text out of pdf/docx/txt uploads
│   └── risk_engine.py                  orchestrates all of the above
├── privacy/
│   └── sanitizer.py                     masks detected PII/secrets
├── models/
│   ├── risk_classifier.py                TF-IDF + Logistic Regression
│   └── train_risk_classifier.py           training entry point
├── backend/
│   ├── main.py                             FastAPI app + WebSocket
│   ├── database.py                          SQLite: audit log, custom rules, users, approvals
│   ├── auth.py                               password hashing + JWT
│   └── llm_providers.py                       Claude / ChatGPT / Gemini forwarding
├── agents/
│   ├── traffic_monitor_agent.py
│   ├── policy_agent.py
│   ├── threat_intel_agent.py
│   └── data_pipeline_agent.py
├── frontend/                                 React + Vite dashboard (light theme)
│   └── src/
│       ├── pages/                             Login, Overview, Gateway, Dashboard, Approvals, Policy, Reports, Integrations
│       ├── components/                         Sidebar, RiskBadge, ScanLine, ProviderSelector, StatCard, TopBar, PageTransition
│       ├── auth/                                AuthContext, ProtectedRoute
│       ├── hooks/useLiveFeed.js                 WebSocket hook
│       └── api/client.js                         backend API calls
├── app.py                                        Streamlit fallback UI (no Node required)
├── checkpoints/                                   trained classifier weights
├── logs/                                           SQLite audit log
└── requirements.txt
```

---

## Setup

### 1. Python backend

```bash
python -m venv venv
source venv/bin/activate        # venv\Scripts\activate.bat on Windows
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

If the spaCy download fails on a restricted network:
```bash
pip install https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl
```

Generate the training data and train the classifier:
```bash
python data/generate_prompts.py
python models/train_risk_classifier.py
```

Start the API:
```bash
uvicorn backend.main:app --reload --port 8000
```
Swagger docs at http://localhost:8000/docs.

### 2. React frontend

Needs Node 18+.

```bash
cd frontend
npm install
npm run dev
```
Opens at http://localhost:5173 and proxies API calls to the backend on
port 8000. Both need to be running for the dashboard to show data.

### 3. (Optional) Streamlit fallback

If Node isn't available, `app.py` at the project root gives a simpler,
zero-JS UI over the same detection logic:
```bash
streamlit run app.py
```
Note: this fallback predates login and LLM forwarding, so it doesn't have
accounts or a provider selector - it's there for a quick detection demo
without installing Node, not a full substitute for the React app.

---

## API reference

| Endpoint | Purpose |
|---|---|
| `POST /auth/register` | Create an employee account |
| `POST /auth/login` | Log in, returns a JWT + user info |
| `GET /auth/me` | Decode the current token |
| `GET /auth/users` | List all accounts (admin only) |
| `GET /providers` | Which LLM providers have a key configured |
| `POST /analyze` | Score a text prompt (optionally forward to an LLM) |
| `POST /analyze-file` | Score an uploaded `.txt`/`.pdf`/`.docx`/`.csv` file |
| `GET /audit-logs` | Recent scan history |
| `GET /stats` | Summary counts |
| `GET /analytics/timeseries` | Hourly activity, bucketed by risk level |
| `GET /analytics/departments` | Per-department request/block counts |
| `GET/POST /rules` | List / add custom detection rules |
| `DELETE /rules/{id}` | Remove a custom rule |
| `PATCH /rules/{id}/toggle` | Enable/disable a rule |
| `GET /export/csv` | Full audit log as CSV |
| `WS /ws/live-feed` | Real-time scan events |
| `GET /approvals?status=pending\|approved\|rejected` | List requests in the approval queue |
| `POST /approvals/{id}/approve` | Approve a blocked request (optionally forwards to an LLM) |
| `POST /approvals/{id}/reject` | Reject a blocked request |
| `POST /agents/{traffic-monitor|policy|threat-intel|data-pipeline}` | Run an agent on demand |

---

## Using real datasets

`data/generate_prompts.py` builds a synthetic dataset because real
leak-detection corpora (Enron emails, PII benchmark sets, GitHub secret
leaks) need separate downloads and licenses. To swap in real data, produce
a CSV with `prompt`, `category`, `risk_level` columns matching
`data/prompts.csv` and re-run `train_risk_classifier.py` — nothing else
needs to change.

## Upgrading the classifier

See `models/upgrade_notes.md` for notes on moving from TF-IDF + Logistic
Regression to a fine-tuned transformer once you have more data and a GPU.

## Known simplifications

- SQLite instead of Postgres (swap the `DATABASE_URL` in
  `backend/database.py` — SQLAlchemy handles the rest)
- Agents run on demand rather than on a schedule (wire into cron / Airflow
  for production)
- JWT secret defaults to a randomly generated value if
  `SENTINEL_JWT_SECRET` isn't set, which means sessions don't survive a
  server restart. Set it explicitly for anything beyond local demo use
- The default admin account (`admin` / `admin123`) is seeded on first run
  purely so the app isn't locked out of its own admin pages - change the
  password immediately in any shared environment
- No password reset flow, no email verification, no rate limiting on
  login attempts - this is a demo-grade auth system, not a
  production-hardened one
- LLM forwarding requires you to supply your own API key(s); nothing is
  forwarded anywhere without one configured, and the UI disables provider
  options it can't actually reach
