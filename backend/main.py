import asyncio
import sys
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# psycopg3 requires SelectorEventLoop on Windows
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from api.routes import chat, tasks, reports, auth_routes
from data.medicaid_report_fetcher import seed_knowledge_base
from storage.supabase_client import get_pool, close_pool

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
    allow_origins=["http://localhost:5173", "https://pbm.avanon.ai"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_routes.router)
app.include_router(chat.router)
app.include_router(tasks.router)
app.include_router(reports.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "avanon-pbm"}
