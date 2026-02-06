from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.accounts_v2 import router as accounts_v2_router
from app.config import get_settings
from app.api.auth import router as auth_router
from app.api.auth_v2 import router as auth_v2_router
from app.api.accounts import router as accounts_router
from app.api.public import router as public_router
from app.services.security_store import is_redis_available

settings = get_settings()

app = FastAPI(
    title="Copy Trade Dashboard API",
    description="API para gerenciamento de contas de copy trade",
    version="2.0.0",
    docs_url="/docs" if settings.docs_enabled else None,
    redoc_url="/redoc" if settings.docs_enabled else None,
    openapi_url="/openapi.json" if settings.docs_enabled else None,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", settings.csrf_header_name],
)

# Routers (v2 first, then v1 deprecated)
app.include_router(auth_v2_router)
app.include_router(accounts_v2_router)
app.include_router(auth_router)
app.include_router(accounts_router)
app.include_router(public_router)


@app.on_event("startup")
async def startup_security_checks() -> None:
    if settings.app_env == "production" and not is_redis_available():
        raise RuntimeError("Redis must be reachable in production")


@app.middleware("http")
async def v1_deprecation_middleware(request: Request, call_next):
    path = request.url.path
    is_v1_path = path.startswith("/api/auth") or path.startswith("/api/admin")
    now = datetime.now(timezone.utc)

    if is_v1_path and now >= settings.v1_sunset_at:
        return JSONResponse(
            status_code=410,
            content={"detail": "API v1 descontinuada. Use /api/v2."},
            headers={
                "Deprecation": "true",
                "Sunset": settings.v1_sunset_http
            }
        )

    response = await call_next(request)
    if is_v1_path:
        response.headers["Deprecation"] = "true"
        response.headers["Sunset"] = settings.v1_sunset_http
    return response


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "version": "2.0.0"}


@app.get("/")
async def root():
    return {
        "message": "Copy Trade Dashboard API",
        "docs": "/docs" if settings.docs_enabled else None,
        "health": "/api/health"
    }
