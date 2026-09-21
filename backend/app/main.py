'''import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import Counter, Histogram, make_asgi_app
from app.core.config import settings
from app.api.v1 import auth, children, chapters, lessons, learning
from app.api.v1.router import router as api_router

from fastapi import APIRouter

from app.api.v1.auth import router as auth_router

router = APIRouter()

router.include_router(
    auth_router,
    prefix="/auth",
    tags=["Authentication"],
)
api_router.include_router(...)
app = FastAPI(
    title="AI Parent Tutor"
)

app.include_router(
    api_router,
    prefix="/api/v1"
)
REQUESTS=Counter("http_requests_total","HTTP requests",["method","path","status"])
LATENCY=Histogram("http_request_duration_seconds","HTTP request latency",["path"])
app=FastAPI(title=settings.app_name,version="1.0.0",docs_url="/docs" if settings.environment!="production" else None)
app.add_middleware(CORSMiddleware,allow_origins=[x.strip() for x in settings.allowed_origins.split(",")],allow_credentials=True,allow_methods=["*"],allow_headers=["*"])
@app.middleware("http")
async def metrics(request:Request,call_next):
    start=time.perf_counter()
    response=await call_next(request)
    path=request.url.path; LATENCY.labels(path=path).observe(time.perf_counter()-start); REQUESTS.labels(request.method,path,str(response.status_code)).inc(); return response
app.include_router(auth.router,prefix="/api/v1/auth",tags=["auth"])
app.include_router(children.router,prefix="/api/v1/children",tags=["children"])
app.include_router(chapters.router,prefix="/api/v1/chapters",tags=["chapters"])
app.include_router(lessons.router,prefix="/api/v1/lessons",tags=["lessons"])
app.include_router(learning.router,prefix="/api/v1/learning",tags=["learning"])
@app.get("/health")
async def health(): return {"status":"ok","environment":settings.environment}
app.mount("/metrics",make_asgi_app())'''


import time

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from prometheus_client import Counter, Histogram, make_asgi_app

from app.core.config import settings
from app.api.v1 import auth, children, chapters, lessons, learning
from starlette.middleware.sessions import SessionMiddleware
from app.api.v1 import videos


# --------------------------------------------------
# Metrics
# --------------------------------------------------

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


# --------------------------------------------------
# FastAPI application
# --------------------------------------------------

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    docs_url="/docs" if settings.environment != "production" else None,
)


# --------------------------------------------------
# CORS
# --------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key=settings.secret_key,
)

# --------------------------------------------------
# Metrics middleware
# --------------------------------------------------

@app.middleware("http")
async def metrics(request: Request, call_next):
    start = time.perf_counter()

    response = await call_next(request)

    path = request.url.path

    LATENCY.labels(
        path=path
    ).observe(
        time.perf_counter() - start
    )

    REQUESTS.labels(
        request.method,
        path,
        str(response.status_code),
    ).inc()

    return response


# --------------------------------------------------
# API ROUTES
# --------------------------------------------------

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


# --------------------------------------------------
# Health check
# --------------------------------------------------

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "environment": settings.environment,
    }


# --------------------------------------------------
# Prometheus metrics
# --------------------------------------------------

app.mount(
    "/metrics",
    make_asgi_app(),
)

app.include_router(
    videos.router,
    prefix="/api/v1/videos",
    tags=["videos"],
)