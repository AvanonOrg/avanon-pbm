# Avanon PBM Intelligence — Project Reference

## Architecture

```
avanon-pbm/
├── backend/          FastAPI app — deployed on Railway (port 8080)
│   ├── main.py       Entry point, mounts routers
│   ├── agents/       Claude orchestration (orchestrator.py, system_prompt.py, tool_definitions.py)
│   ├── api/          HTTP routes + auth middleware (JWT)
│   ├── data/         NADAC fetcher, GoodRx scraper, Medicaid report fetcher
│   ├── analysis/     Spread calculator, report builder
│   ├── storage/      Supabase client, KB cache, models
│   ├── lib/          PDF generation (generate_report.py), font loader
│   └── services/     pdf_builder.py (spec builder)
└── frontend/         Next.js 16 app — deployed on Vercel
    ├── app/          App Router pages and API routes
    │   └── api/chat/stream/route.ts   SSE proxy → Railway backend
    └── components/   UI components
```

## Live URLs
- **Frontend (Vercel)**: https://avanon-pbm.vercel.app
- **Backend (Railway)**: https://avanon-pbm-production.up.railway.app

## Auth
JWT-based. Demo credentials in `backend/api/middleware/auth.py`:
- `demo@avanon.ai` / `pbm2026!` (tenant: tenant_demo)
- `costplus@avanon.ai` / `markc2026!` (tenant: tenant_costplus)

## Environment Variables

**Railway (backend)**:
- `ANTHROPIC_API_KEY` — Claude API key
- `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` — database
- `CORS_ORIGINS` — comma-separated allowed origins (must include Vercel URL)
- `JWT_SECRET` — token signing key

**Vercel (frontend)**:
- `NEXT_PUBLIC_API_URL` — Railway backend URL (https://avanon-pbm-production.up.railway.app)

## Deployment

### Railway (backend) — auto-deploys on git push
```bash
git push origin master
# Railway watches master branch of AvanonOrg/avanon-pbm
# Monitor at: https://railway.app/project/2a60140d-d6f2-4156-aeea-c6774382541f
```

### Vercel (frontend) — manual deploy
```bash
cd frontend
vercel --prod
# Or use the /deploy slash command
```

### IDs (do not change)
| Platform | Key | Value |
|----------|-----|-------|
| Railway  | Project ID | `2a60140d-d6f2-4156-aeea-c6774382541f` |
| Railway  | Service ID | `785e7ef9-b34f-455d-af5b-f1d1c527dce7` |
| Railway  | Environment ID | `c0717d93-a645-4754-8b0f-8ff14f2085ec` |
| Vercel   | Project ID | `prj_urHZPToKj7aC5AKPzI4XEJRlyRKp` |
| Vercel   | Team/Org ID | `team_42zLZehdoy9fx3H1sPjVQLeL` |

## Running Locally
```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8080

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
# Runs at http://localhost:3000
# Needs NEXT_PUBLIC_API_URL=http://localhost:8080 in frontend/.env.local
```

## Key Files for Common Tasks
| Task | File |
|------|------|
| Change AI behavior / tools | `backend/agents/system_prompt.py`, `backend/agents/tool_definitions.py` |
| Change AI orchestration | `backend/agents/orchestrator.py` |
| Change PDF report layout | `backend/lib/generate_report.py` |
| Change PDF report data spec | `backend/services/pdf_builder.py` |
| Change login / users | `backend/api/middleware/auth.py` |
| Change frontend chat UI | `frontend/app/page.tsx` or `frontend/components/` |
| Add/change API endpoints | `backend/api/routes/` |

## New Developer Setup
Run `bash scripts/setup.sh` — installs Railway and Vercel CLIs, authenticates via browser OAuth, and links both projects so `/deploy` works immediately.
