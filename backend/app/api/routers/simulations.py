from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db import get_db
from app.models import Export, JudgeEvaluation, Matter, SimulationFinding, SimulationRun, SimulationRound, SimulationTurn
from app.schemas import ExportRead, SimulationDetail, SimulationRunCreate, SimulationRunRead
from app.services.memo import export_vulnerability_memo
from app.services.simulation import create_and_run_simulation

router = APIRouter(tags=["simulations"])


@router.get("/matters/{matter_id}/simulations", response_model=list[SimulationRunRead])
def list_simulations(matter_id: str, db: Session = Depends(get_db)) -> list[SimulationRun]:
    return list(db.scalars(select(SimulationRun).where(SimulationRun.matter_id == matter_id).order_by(SimulationRun.created_at.desc())).all())


@router.post("/matters/{matter_id}/simulations", response_model=SimulationDetail)
async def create_simulation(matter_id: str, payload: SimulationRunCreate, db: Session = Depends(get_db)) -> SimulationDetail:
    matter = db.get(Matter, matter_id)
    if not matter:
        raise HTTPException(status_code=404, detail="Matter not found")
    run = await create_and_run_simulation(db, matter_id, payload.config)
    return load_detail(db, run.id)


@router.get("/simulations/{simulation_id}", response_model=SimulationDetail)
def get_simulation(simulation_id: str, db: Session = Depends(get_db)) -> SimulationDetail:
    return load_detail(db, simulation_id)


@router.get("/simulations/{simulation_id}/transcript", response_model=list[dict])
def get_transcript(simulation_id: str, db: Session = Depends(get_db)) -> list[dict]:
    run = db.get(SimulationRun, simulation_id)
    if not run:
        raise HTTPException(status_code=404, detail="Simulation not found")
    turns = list(db.scalars(select(SimulationTurn).where(SimulationTurn.simulation_id == simulation_id).order_by(SimulationTurn.round_number, SimulationTurn.turn_number)).all())
    return [
        {
            "round_number": turn.round_number,
            "turn_number": turn.turn_number,
            "agent_name": turn.agent_role,
            "model": f"{turn.model_provider}/{turn.model_name}",
            "output": turn.output,
            "sources_cited": turn.sources_cited,
            "new_findings": turn.new_findings,
        }
        for turn in turns
    ]


@router.post("/simulations/{simulation_id}/export", response_model=ExportRead)
def export_simulation(simulation_id: str, db: Session = Depends(get_db)) -> ExportRead:
    try:
        export = export_vulnerability_memo(db, simulation_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Simulation not found") from None
    content = open(export.storage_path).read()
    return ExportRead.model_validate(export).model_copy(update={"content": content})


def load_detail(db: Session, simulation_id: str) -> SimulationDetail:
    run = db.scalars(select(SimulationRun).where(SimulationRun.id == simulation_id).options(selectinload(SimulationRun.rounds))).first()
    if not run:
        raise HTTPException(status_code=404, detail="Simulation not found")
    rounds = list(db.scalars(select(SimulationRound).where(SimulationRound.simulation_id == simulation_id).order_by(SimulationRound.round_number)).all())
    turns = list(db.scalars(select(SimulationTurn).where(SimulationTurn.simulation_id == simulation_id).order_by(SimulationTurn.round_number, SimulationTurn.turn_number)).all())
    findings = list(db.scalars(select(SimulationFinding).where(SimulationFinding.simulation_id == simulation_id)).all())
    judges = list(db.scalars(select(JudgeEvaluation).where(JudgeEvaluation.simulation_id == simulation_id)).all())
    detail = SimulationDetail.model_validate(run)
    detail.rounds = rounds
    detail.turns = turns
    detail.findings = findings
    detail.judge_evaluations = judges
    return detail

