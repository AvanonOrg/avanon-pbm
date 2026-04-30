import asyncio
import sys
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# psycopg3 requires SelectorEventLoop on Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from config import get_settings
from api.routes import chat, tasks, reports, auth_routes, prospects
from data.medicaid_report_fetcher import seed_knowledge_base
from storage.supabase_client import get_pool, close_pool
from api.routes.reports import _render_pdf
from api.middleware.auth import get_tenant_id
from fastapi import Depends

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Connecting to Supabase PostgreSQL...")
    await get_pool()
    logger.info("Seeding Medicaid PBM knowledge base...")
    await seed_knowledge_base()
    logger.info("PBM Intelligence agent ready.")
    yield
    await close_pool()
    logger.info("Shutting down.")


app = FastAPI(title="Avanon PBM Pass-Through Intelligence", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in get_settings().cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(chat.router)
app.include_router(tasks.router)
app.include_router(reports.router)
app.include_router(prospects.router)


@app.post("/api/pdf")
async def generate_pdf(report: dict, tenant_id: str = Depends(get_tenant_id)):
    from services.pdf_builder import build_pdf_spec
    spec = build_pdf_spec(report)
    report_id = report.get("report_id", "report")
    return await _render_pdf(spec, f"pbm-report-{report_id}.pdf")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "avanon-pbm"}
