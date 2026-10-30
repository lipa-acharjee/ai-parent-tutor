
import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, make_asgi_app
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import settings
from app.api.v1 import (
    auth,
    children,
    chapters,
    lessons,
    learning,
    videos,
    shared_videos,
)
from app.api.v1.kling import router as kling_router


# ============================================================
# METRICS
# ============================================================

REQUESTS = Counter(
    "http_requests_total",
    "HTTP requests",
    ["method", "path", "status"],
)

LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["path"],
)


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    docs_url="/docs",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in settings.allowed_origins.split(",")
        if origin.strip()
    ],
    allow_origin_regex=r"^http://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# SESSION MIDDLEWARE
# ============================================================

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
)


# ============================================================
# METRICS MIDDLEWARE
# ============================================================

@app.middleware("http")
async def metrics(request: Request, call_next):
    start = time.perf_counter()

    response = await call_next(request)

    path = request.url.path

    LATENCY.labels(
        path=path,
    ).observe(
        time.perf_counter() - start,
    )

    REQUESTS.labels(
        request.method,
        path,
        str(response.status_code),
    ).inc()

    return response


# ============================================================
# API ROUTES
# ============================================================

app.include_router(
    auth.router,
    prefix="/api/v1/auth",
    tags=["auth"],
)

app.include_router(
    children.router,
    prefix="/api/v1/children",
    tags=["children"],
)

app.include_router(
    chapters.router,
    prefix="/api/v1/chapters",
    tags=["chapters"],
)

app.include_router(
    lessons.router,
    prefix="/api/v1/lessons",
    tags=["lessons"],
)

app.include_router(
    learning.router,
    prefix="/api/v1/learning",
    tags=["learning"],
)

app.include_router(
    shared_videos.router,
    prefix="/api/v1/shared-videos",
    tags=["Shared Videos"],
)

app.include_router(
    videos.router,
    prefix="/api/v1/videos",
    tags=["videos"],
)

app.include_router(
    kling_router,
    prefix="/api/v1/kling",
    tags=["Kling"],
)


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "environment": settings.environment,
    }


# ============================================================
# PROMETHEUS METRICS ENDPOINT
# ============================================================

app.mount(
    "/metrics",
    make_asgi_app(),
)
