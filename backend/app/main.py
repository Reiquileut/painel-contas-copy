from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.api.auth import router as auth_router
from app.api.accounts import router as accounts_router
from app.api.public import router as public_router

settings = get_settings()

app = FastAPI(
    title="Copy Trade Dashboard API",
    description="API para gerenciamento de contas de copy trade",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth_router)
app.include_router(accounts_router)
app.include_router(public_router)


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/")
async def root():
    return {
        "message": "Copy Trade Dashboard API",
        "docs": "/docs",
        "health": "/api/health"
    }
