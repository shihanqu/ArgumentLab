from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import AgentRouting, Provider
from app.schemas import (
    AgentRoutingRead,
    AgentRoutingUpdate,
    DiagnosticRequest,
    DiagnosticResult,
    JudgePersonaRead,
    ProviderCreate,
    ProviderRead,
    ProviderUpdate,
)
from app.services.model_gateway import ModelGateway
from app.services.simulation import JUDGE_PERSONAS, seed_model_routing

router = APIRouter(prefix="/model-routing", tags=["model-routing"])


@router.get("/providers", response_model=list[ProviderRead])
def list_providers(db: Session = Depends(get_db)) -> list[ProviderRead]:
    seed_model_routing(db)
    providers = list(db.scalars(select(Provider).order_by(Provider.created_at.asc())).all())
    return [provider_read(provider) for provider in providers]


@router.post("/providers", response_model=ProviderRead)
def create_provider(payload: ProviderCreate, db: Session = Depends(get_db)) -> ProviderRead:
    provider = Provider(**payload.model_dump())
    db.add(provider)
    db.commit()
    db.refresh(provider)
    return provider_read(provider)


@router.put("/providers/{provider_id}", response_model=ProviderRead)
def update_provider(provider_id: str, payload: ProviderUpdate, db: Session = Depends(get_db)) -> ProviderRead:
    provider = db.get(Provider, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    for key, value in payload.model_dump().items():
        setattr(provider, key, value)
    db.commit()
    db.refresh(provider)
    return provider_read(provider)


@router.delete("/providers/{provider_id}", status_code=204)
def delete_provider(provider_id: str, db: Session = Depends(get_db)) -> None:
    provider = db.get(Provider, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    if provider.provider_type == "mock":
        raise HTTPException(status_code=400, detail="The default mock provider cannot be deleted.")
    for route in db.scalars(select(AgentRouting).where((AgentRouting.default_provider_id == provider_id) | (AgentRouting.fallback_provider_id == provider_id))).all():
        if route.default_provider_id == provider_id:
            route.default_provider_id = None
        if route.fallback_provider_id == provider_id:
            route.fallback_provider_id = None
    db.delete(provider)
    db.commit()


@router.post("/providers/{provider_id}/diagnostics", response_model=DiagnosticResult)
async def run_diagnostic(provider_id: str, payload: DiagnosticRequest, db: Session = Depends(get_db)) -> DiagnosticResult:
    provider = db.get(Provider, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    result = await ModelGateway().diagnostic(provider, payload.kind)
    provider.last_error = result.get("last_error")
    provider.diagnostics = {**(provider.diagnostics or {}), payload.kind: result}
    db.commit()
    return DiagnosticResult(**result)


@router.get("/agents", response_model=list[AgentRoutingRead])
def list_agent_routing(db: Session = Depends(get_db)) -> list[AgentRouting]:
    seed_model_routing(db)
    return list(db.scalars(select(AgentRouting).order_by(AgentRouting.agent_name.asc())).all())


@router.put("/agents/{agent_id}", response_model=AgentRoutingRead)
def update_agent_routing(agent_id: str, payload: AgentRoutingUpdate, db: Session = Depends(get_db)) -> AgentRouting:
    route = db.get(AgentRouting, agent_id)
    if not route:
        raise HTTPException(status_code=404, detail="Agent route not found")
    for key, value in payload.model_dump().items():
        setattr(route, key, value)
    db.commit()
    db.refresh(route)
    return route


@router.get("/judge-personas", response_model=list[JudgePersonaRead])
def list_judge_personas() -> list[JudgePersonaRead]:
    return [JudgePersonaRead(id=persona_id, **persona) for persona_id, persona in JUDGE_PERSONAS.items()]


def provider_read(provider: Provider) -> ProviderRead:
    data = ProviderRead.model_validate(provider).model_dump()
    data["has_secret"] = bool(provider.api_key)
    return ProviderRead(**data)

