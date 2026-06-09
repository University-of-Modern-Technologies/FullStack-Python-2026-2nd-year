"""Точка входу FastAPI-додатка Secured Todo API."""
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from src.conf.config import settings
from src.database.db import get_db
from src.limiter import limiter
from src.middleware.ip_block import IpBlockMiddleware
from src.routes import access, auth, todos, users
from src.services.cache import cache_service

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Закриває зовнішні ресурси застосунку під час завершення FastAPI."""
    yield
    await cache_service.close()


app = FastAPI(title="Secured Todo API", lifespan=lifespan)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- IP blacklist ---
app.add_middleware(IpBlockMiddleware, blocked_ips_path=settings.blocked_ips_path)

# --- Rate limit / slowapi ---
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Формує JSON-відповідь для помилки перевищення rate limit."""
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"error": "Перевищено ліміт запитів. Спробуйте пізніше."},
    )


app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(todos.router, prefix="/api")
app.include_router(access.router, prefix="/api")


@app.get("/")
def read_root():
    """Повертає коротке інформаційне повідомлення з кореневого endpoint-а."""
    return {"message": "TODO Application v1.0 (lesson 10)"}


@app.get("/healthz")
async def healthz():
    """Повертає базовий healthcheck без перевірки зовнішніх сервісів."""
    return {"status": "ok", "message": "Application is running"}


@app.get("/readyz")
async def readyz(db: AsyncSession = Depends(get_db)):
    """Готовність: Postgres + Redis."""
    try:
        result = await db.execute(text("SELECT 1"))
        if result.fetchone() is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database is not configured correctly",
            )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Error connecting to the database")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error connecting to the database",
        )

    if not await cache_service.ping():
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Redis is not available",
        )

    return {"status": "ok", "message": "Application is ready (DB + Redis)"}
