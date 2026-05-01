<div align="center">

<img src="https://img.shields.io/badge/Avanon-PBM_Intelligence-0053A0?style=for-the-badge&labelColor=0C2340" height="40" />

<br/>

**AI-powered platform that exposes hidden pharmacy benefit manager spread pricing — and quantifies exactly how much your health plan is overpaying.**

<br/>

[![Claude AI](https://img.shields.io/badge/Claude_AI-Anthropic-6B48FF?style=flat-square&logo=anthropic&logoColor=white)](https://anthropic.com)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-16-000000?style=flat-square&logo=next.js&logoColor=white)](https://nextjs.org)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat-square&logo=python&logoColor=white)](https://python.org)
[![Railway](https://img.shields.io/badge/Backend-Railway-0B0D0E?style=flat-square&logo=railway&logoColor=white)](https://railway.app)
[![Vercel](https://img.shields.io/badge/Frontend-Vercel-000000?style=flat-square&logo=vercel&logoColor=white)](https://vercel.com)
[![Supabase](https://img.shields.io/badge/Database-Supabase-3ECF8E?style=flat-square&logo=supabase&logoColor=white)](https://supabase.com)

<br/>

[**Live Demo →**](https://avanon-pbm.vercel.app) &nbsp;·&nbsp; [Quick Start](#quick-start) &nbsp;·&nbsp; [Architecture](#architecture) &nbsp;·&nbsp; [API Reference](#api-reference)

</div>

---

## The $200M Problem

The three largest pharmacy benefit managers — CVS Caremark, Express Scripts, and OptumRx — control **79% of US prescriptions**. Under spread pricing, they charge your health plan far more than they pay the pharmacy, pocketing the difference silently.

| What your PBM charges your plan | What your PBM pays the pharmacy | PBM keeps |
|---|---|---|
| $312.00 | $14.82 (NADAC rate) | **$297.18 per fill** |

State Medicaid audits have quantified the scale: **$224.8M in Ohio alone** (2018), **$123M in Kentucky** (2019). Self-insured employers face the same problem with zero visibility.

**Avanon fixes that.**

---

## What It Does

Avanon PBM Intelligence is a Claude AI–powered chat interface that lets benefits brokers and self-insured employers ask plain-language questions about drug pricing, then automatically:

1. **Fetches NADAC** — the weekly CMS-published true pharmacy acquisition cost (the pass-through benchmark)
2. **Scrapes market prices** from GoodRx across major pharmacy chains
3. **Calculates the spread** — dollar and percentage markup above NADAC
4. **Flags discrepancies** — LOW / MEDIUM / HIGH / CRITICAL tiers
5. **Projects annual savings** — modeled for 100 plan members on a pass-through contract
6. **Generates a PDF report** — pharma-grade discrepancy report ready to share with stakeholders

---

## Features

### AI Chat Interface
- Streaming responses via Server-Sent Events (SSE)
- Full conversation memory per session (Supabase-backed)
- Seamlessly falls back to Claude's own pricing knowledge when live data is unavailable
- Proactively offers to generate formal reports after each analysis

### Drug Pricing Engine
- **NADAC integration** — live CMS government data, queried by drug name or NDC
- **GoodRx scraper** — parses `__NEXT_DATA__` JSON and visible price text from GoodRx pages
- **Spread calculator** — four-tier risk classification (< 20% LOW → > 500% CRITICAL)
- **Medicaid citations** — auto-attaches relevant state audit references for credibility

### Report Generation
- **Pharmaceutical-grade PDF** — Pfizer/BioNTech-inspired layout with Noto Sans typography
- Executive summary, KPI banner, risk-coded drug table (landscape), bar charts, regulatory citations
- Fonts downloaded automatically at first run; falls back to system fonts gracefully
- Reports saved to Supabase and downloadable via the UI

### Monitoring
- Create recurring price monitoring tasks for any drug
- Configurable frequency: daily / weekly / biweekly / monthly
- Task status tracked per tenant in Supabase

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User (Browser)                           │
└───────────────────┬─────────────────────────────────────────────┘
                    │  HTTPS + SSE streaming
┌───────────────────▼──────────────┐   ┌──────────────────────────┐
│      Next.js 16 (Vercel)         │   │   Supabase (PostgreSQL)   │
│  app/page.tsx — chat UI          │   │  • conversations         │
│  app/api/chat/stream/route.ts    │   │  • reports               │
│    SSE proxy → Railway backend   │   │  • tasks                 │
└───────────────────┬──────────────┘   │  • pricing snapshots     │
                    │  JWT + SSE       │  • knowledge base cache  │
┌───────────────────▼──────────────┐   └───────────▲──────────────┘
│      FastAPI (Railway :8080)     │               │
│                                  │               │
│  ┌─────────────────────────────┐ │               │
│  │   Claude AI Orchestrator    │ │               │
│  │   (agents/orchestrator.py)  │◄├───────────────┘
│  │                             │ │
│  │  Tools:                     │ │
│  │  • search_knowledge_base    │ │
│  │  • fetch_nadac_baseline ────┼─┼──► CMS data.cms.gov (NADAC)
│  │  • search_drug_prices ──────┼─┼──► GoodRx (HTTP scrape)
│  │  • create_monitoring_task   │ │
│  │  • generate_discrepancy_    │ │
│  │    report ─────────────────┼─┼──► ReportLab PDF → Supabase
│  └─────────────────────────────┘ │
└──────────────────────────────────┘
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| **AI** | Claude claude-sonnet-4-6 via Anthropic SDK (streaming tool use) |
| **Backend** | FastAPI 0.115, Python 3.11, Uvicorn |
| **Frontend** | Next.js 16, TypeScript, Tailwind CSS |
| **Database** | Supabase (PostgreSQL) |
| **PDF** | ReportLab 4.2, Matplotlib (charts), Noto Sans fonts |
| **Auth** | JWT (python-jose) |
| **Backend host** | Railway (auto-deploy on `git push`) |
| **Frontend host** | Vercel |

---

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- A [Supabase](https://supabase.com) project
- An [Anthropic API key](https://console.anthropic.com)

### 1. Clone

```bash
git clone https://github.com/AvanonOrg/avanon-pbm.git
cd avanon-pbm
```

### 2. Backend

```bash
cd backend
pip install -r requirements.txt
```

Create `backend/.env`:

```env
ANTHROPIC_API_KEY=sk-ant-...
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
JWT_SECRET=your-secret-key
CORS_ORIGINS=http://localhost:3000
CLAUDE_MODEL=claude-sonnet-4-6
```

```bash
uvicorn main:app --reload --port 8080
# API running at http://localhost:8080
```

### 3. Frontend

```bash
cd frontend
npm install
```

Create `frontend/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8080
```

```bash
npm run dev
# UI running at http://localhost:3000
```

### 4. Database schema

Run `schema.sql` in your Supabase SQL editor to create the required tables.

---

## Demo Credentials

The live demo at [avanon-pbm.vercel.app](https://avanon-pbm.vercel.app) accepts:

| Email | Password | Tenant |
|-------|----------|--------|
| `demo@avanon.ai` | `pbm2026!` | tenant_demo |
| `costplus@avanon.ai` | `markc2026!` | tenant_costplus |

---

## Example Queries

```
What is the spread on lisinopril 10mg for 30 days?

Compare our plan's metformin costs to NADAC and tell me the annual savings if we switch to pass-through pricing.

Monitor atorvastatin 20mg weekly and alert me if the spread exceeds 200%.

Analyze omeprazole, metformin, and atorvastatin and generate a report I can share with the CFO.
```

---

## API Reference

Base URL: `https://avanon-pbm-production.up.railway.app`

### Authentication

```http
POST /auth/login
Content-Type: application/json

{ "email": "demo@avanon.ai", "password": "pbm2026!" }
```

Returns `{ "access_token": "...", "token_type": "bearer" }`.

Include in all subsequent requests:
```
Authorization: Bearer <token>
```

### Chat (streaming)

```http
POST /chat/stream
Authorization: Bearer <token>
Content-Type: application/json

{
  "message": "What is the spread on lisinopril 10mg?",
  "session_id": "optional-session-id",
  "tenant_id": "tenant_demo"
}
```

Returns a stream of SSE events:

| Event type | Payload |
|------------|---------|
| `text_delta` | `{ "delta": "..." }` — streaming token |
| `thinking` | `{ "step": "Fetching NADAC...", "tool": "fetch_nadac_baseline" }` |
| `done` | `{ "reply": "...", "report": {...} \| null, "task_id": "..." }` |
| `error` | `{ "message": "..." }` |

### Download Report PDF

```http
GET /reports/{report_id}/pdf
Authorization: Bearer <token>
```

Returns `application/pdf`.

### Health check

```http
GET /health
```

---

## Deployment

### Automatic (recommended)

Use the `/deploy` Claude Code command from [avanon-tools](https://github.com/AvanonOrg/avanon-tools):

```
/deploy
```

### Manual

**Backend (Railway)** — auto-deploys on every push to `master`:

```bash
git push origin master
# Monitor: https://railway.app/project/2a60140d-d6f2-4156-aeea-c6774382541f
```

**Frontend (Vercel):**

```bash
cd frontend
vercel --prod
```

### Environment variables

Set these in Railway (backend) and Vercel (frontend) dashboards:

**Railway:**
```
ANTHROPIC_API_KEY
SUPABASE_URL
SUPABASE_SERVICE_ROLE_KEY
JWT_SECRET
CORS_ORIGINS      # e.g. https://avanon-pbm.vercel.app
CLAUDE_MODEL      # claude-sonnet-4-6
```

**Vercel:**
```
NEXT_PUBLIC_API_URL   # https://avanon-pbm-production.up.railway.app
```

---

## Project Structure

```
avanon-pbm/
├── backend/
│   ├── main.py                     # FastAPI app entry point
│   ├── agents/
│   │   ├── orchestrator.py         # Claude streaming + tool-use loop
│   │   ├── system_prompt.py        # AI persona and rules
│   │   └── tool_definitions.py     # Claude tool schemas
│   ├── api/
│   │   ├── routes/                 # HTTP endpoints
│   │   └── middleware/auth.py      # JWT validation
│   ├── data/
│   │   ├── nadac_fetcher.py        # CMS NADAC API client
│   │   ├── goodrx_scraper.py       # GoodRx price scraper
│   │   └── medicaid_report_fetcher.py
│   ├── analysis/
│   │   ├── spread_calculator.py    # Spread math + risk classification
│   │   └── report_builder.py       # Assembles DiscrepancyReport model
│   ├── storage/
│   │   ├── supabase_client.py      # DB operations
│   │   ├── kb_cache.py             # Knowledge base cache
│   │   └── models.py               # Pydantic models
│   ├── lib/
│   │   ├── generate_report.py      # ReportLab PDF renderer
│   │   └── font_loader.py          # Noto Sans downloader + fallback
│   └── services/
│       └── pdf_builder.py          # PDF spec builder
└── frontend/
    ├── app/
    │   ├── page.tsx                # Main chat interface
    │   └── api/chat/stream/        # SSE proxy route
    └── components/                 # UI components
```

---

## Key Concepts

**NADAC** — National Average Drug Acquisition Cost, published weekly by CMS. The true cost pharmacies pay for drugs. Any plan price significantly above NADAC represents spread retained by the PBM.

**Spread pricing** — PBM charges the plan more than it pays the pharmacy. The difference is retained as profit without disclosure.

**Pass-through pricing** — Amount charged to plan equals amount paid to pharmacy. PBM earns only a transparent admin fee. Mark Cuban's Cost Plus Drugs operates on this model.

**Spread tiers:**
| Flag | Spread above NADAC | Action |
|------|-------------------|--------|
| LOW | < 20% | Within acceptable tolerance |
| MEDIUM | 20% – 100% | Worth monitoring |
| HIGH | 100% – 500% | Renegotiation warranted |
| CRITICAL | > 500% | Immediate PBM audit recommended |

---

## Related

- [**avanon-tools**](https://github.com/AvanonOrg/avanon-tools) — `/deploy` Claude Code skill and developer onboarding scripts
- [CMS NADAC Data](https://data.cms.gov/provider-summary-by-type-of-service/pharmacy-provider-information/nadac-national-average-drug-acquisition-cost) — Source data
- [Ohio Medicaid PBM Audit (2018)](https://medicaid.ohio.gov) — $224.8M spread documented
- [Kentucky CHFS PBM Audit (2019)](https://chfs.ky.gov) — $123M spread documented

---

<div align="center">
  <sub>Built by <a href="https://github.com/AvanonOrg">Avanon</a> · Powered by <a href="https://anthropic.com">Anthropic Claude</a></sub>
</div>

<!-- deploy-trigger -->
