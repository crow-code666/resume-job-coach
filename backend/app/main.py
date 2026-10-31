from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app import models  # noqa: F401 - registers SQLAlchemy metadata.
from app.api.auth import router as auth_router
from app.api.career_tools import router as career_tools_router
from app.api.resumes import router as resume_router
from app.core.config import get_settings
from app.db import Base, get_engine

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if settings.app_env.casefold() == "development" and settings.database_url:
        Base.metadata.create_all(bind=get_engine())
    yield


app = FastAPI(
    title="CareerLens API",
    version="0.2.0",
    docs_url="/api/docs",
    redoc_url=None,
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.frontend_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["Content-Type", "X-CSRF-Token"],
)
app.include_router(auth_router)
app.include_router(resume_router)
app.include_router(career_tools_router)


@app.get("/api/v1/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/health/database", tags=["health"], response_model=None)
def database_health() -> dict[str, str] | JSONResponse:
    if not settings.database_url:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_configured",
                "reason": "DATABASE_URL is missing or empty. Set it in backend/.env and restart the API.",
            },
        )
    try:
        with get_engine().connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ok"}
    except SQLAlchemyError:
        return JSONResponse(
            status_code=503,
            content={
                "status": "unavailable",
                "reason": "MySQL could not be reached with the configured credentials.",
            },
        )
