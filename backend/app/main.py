import sys
import logging
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import SQLAlchemyError

CURRENT_FILE = Path(__file__).resolve()
BACKEND_DIR = CURRENT_FILE.parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.core.config import settings
from app.db import Base, engine
from app.routers import auth, contracts, documents, obligations, reporting, risk, workflows

logger = logging.getLogger("clm.startup")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO)

app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix=settings.api_prefix)
app.include_router(contracts.router, prefix=settings.api_prefix)
app.include_router(workflows.router, prefix=settings.api_prefix)
app.include_router(documents.router, prefix=settings.api_prefix)
app.include_router(documents.clause_router, prefix=settings.api_prefix)
app.include_router(obligations.router, prefix=settings.api_prefix)
app.include_router(reporting.router, prefix=settings.api_prefix)
app.include_router(risk.router, prefix=settings.api_prefix)


@app.on_event("startup")
def init_database() -> None:
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database connection established. Schema initialization completed.")
    except SQLAlchemyError as exc:
        logger.warning(
            "Database is unavailable at startup. API will continue running, but database-backed endpoints may fail until DB is reachable. Error: %s",
            exc,
        )


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
