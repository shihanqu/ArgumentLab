from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import benchmarks, documents, emails, matters, model_routing, simulations
from app.core.config import get_settings
from app.db import SessionLocal, init_db
from app.services.simulation import seed_model_routing
from app.services.workspace import ensure_workspace

settings = get_settings()

app = FastAPI(
    title="Argument Lab API",
    version="0.1.0",
    description="Local-first legal adversarial reasoning prototype.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(matters.router)
app.include_router(documents.router)
app.include_router(emails.router)
app.include_router(model_routing.router)
app.include_router(simulations.router)
app.include_router(benchmarks.router)


@app.on_event("startup")
def startup() -> None:
    ensure_workspace(settings)
    init_db()
    with SessionLocal() as db:
        seed_model_routing(db)


@app.get("/health")
def health() -> dict:
    return {
        "ok": True,
        "auth_mode": settings.auth_mode,
        "storage_mode": settings.storage_mode,
        "workspace": str(settings.workspace),
        "model_gateway": settings.model_gateway,
    }

