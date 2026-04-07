import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from app.api.v1.router import api_router
from app.config import settings
from app.core.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(
    level=logging.INFO if not settings.is_production else logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


# ---------------------------------------------------------------------------
# Rate limiting (in-memory, per-IP)
# ---------------------------------------------------------------------------

from cachetools import TTLCache
import time

_rate_buckets: TTLCache[str, list[float]] = TTLCache(maxsize=10000, ttl=60)

RATE_LIMITS: dict[str, int] = {
    "auth": 10,      # /auth/* — 10 req/min
    "search": 30,    # /programs?q= — 30 req/min
    "default": 100,  # everything else — 100 req/min
}


def _get_rate_key(request: Request) -> tuple[str, int]:
    path = request.url.path
    ip = request.client.host if request.client else "unknown"
    if "/auth/" in path:
        return f"auth:{ip}", RATE_LIMITS["auth"]
    if "/programs" in path and request.query_params.get("q"):
        return f"search:{ip}", RATE_LIMITS["search"]
    return f"default:{ip}", RATE_LIMITS["default"]


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        key, limit = _get_rate_key(request)
        now = time.time()

        hits = _rate_buckets.get(key, [])
        hits = [t for t in hits if now - t < 60]

        if len(hits) >= limit:
            return Response(
                content='{"detail":"Rate limit exceeded"}',
                status_code=429,
                media_type="application/json",
                headers={"Retry-After": "60"},
            )

        hits.append(now)
        _rate_buckets[key] = hits

        return await call_next(request)


# ---------------------------------------------------------------------------
# Security headers
# ---------------------------------------------------------------------------


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if settings.is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="SearchPro API",
    description="정부지원사업·공모전 통합 검색 플랫폼",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

# Middleware (order matters — last added = first executed)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok", "env": settings.ENV}
