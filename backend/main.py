import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.config import settings
from backend.models import Base, engine
from backend.routers import admin
from backend.services.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Placement Compliance API starting...")
    Base.metadata.create_all(bind=engine)
    start_scheduler()
    yield
    stop_scheduler()
    logger.info("🛑 API shutting down.")


app = FastAPI(
    title="Placement Compliance & Nudge Bot API",
    version="1.0.0",
    description="Admin API for managing student placement drives, CSV uploads, and automated Telegram nudges.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(admin.router)


@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "version": "1.0.0"}
