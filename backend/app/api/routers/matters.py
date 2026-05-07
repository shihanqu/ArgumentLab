from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import EmailEvent, Matter, SimulationRun
from app.models import Document as DocumentModel
from app.schemas import MatterCreate, MatterRead, MatterSummary
from app.services.workspace import delete_matter_files

router = APIRouter(prefix="/matters", tags=["matters"])


@router.get("", response_model=list[MatterSummary])
def list_matters(db: Session = Depends(get_db)) -> list[MatterSummary]:
    matters = list(db.scalars(select(Matter).order_by(Matter.updated_at.desc())).all())
    summaries = []
    for matter in matters:
        summaries.append(
            MatterSummary(
                **MatterRead.model_validate(matter).model_dump(),
                document_count=db.query(DocumentModel).filter(DocumentModel.matter_id == matter.id).count(),
                email_count=db.query(EmailEvent).filter(EmailEvent.matter_id == matter.id).count(),
                simulation_count=db.query(SimulationRun).filter(SimulationRun.matter_id == matter.id).count(),
            )
        )
    return summaries


@router.post("", response_model=MatterRead)
def create_matter(payload: MatterCreate, db: Session = Depends(get_db)) -> Matter:
    matter = Matter(name=payload.name, description=payload.description)
    db.add(matter)
    db.commit()
    db.refresh(matter)
    return matter


@router.get("/{matter_id}", response_model=MatterSummary)
def get_matter(matter_id: str, db: Session = Depends(get_db)) -> MatterSummary:
    matter = db.get(Matter, matter_id)
    if not matter:
        raise HTTPException(status_code=404, detail="Matter not found")
    return MatterSummary(
        **MatterRead.model_validate(matter).model_dump(),
        document_count=db.query(DocumentModel).filter(DocumentModel.matter_id == matter.id).count(),
        email_count=db.query(EmailEvent).filter(EmailEvent.matter_id == matter.id).count(),
        simulation_count=db.query(SimulationRun).filter(SimulationRun.matter_id == matter.id).count(),
    )


@router.delete("/{matter_id}", status_code=204)
def delete_matter(matter_id: str, db: Session = Depends(get_db)) -> None:
    matter = db.get(Matter, matter_id)
    if not matter:
        raise HTTPException(status_code=404, detail="Matter not found")
    db.delete(matter)
    db.commit()
    delete_matter_files(matter_id)

