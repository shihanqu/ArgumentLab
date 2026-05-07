from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import EmailEvent, Matter
from app.schemas import CopiedEmailThread, EmailEventRead
from app.services.email_parser import parse_copied_thread

router = APIRouter(prefix="/matters/{matter_id}/emails", tags=["emails"])


@router.get("", response_model=list[EmailEventRead])
def list_email_events(matter_id: str, db: Session = Depends(get_db)) -> list[EmailEvent]:
    return list(
        db.scalars(
            select(EmailEvent)
            .where(EmailEvent.matter_id == matter_id)
            .order_by(EmailEvent.normalized_timestamp.asc().nulls_last(), EmailEvent.created_at.asc())
        ).all()
    )


@router.post("/copied-thread", response_model=list[EmailEventRead])
def ingest_copied_thread(matter_id: str, payload: CopiedEmailThread, db: Session = Depends(get_db)) -> list[EmailEvent]:
    matter = db.get(Matter, matter_id)
    if not matter:
        raise HTTPException(status_code=404, detail="Matter not found")
    created: list[EmailEvent] = []
    for parsed in parse_copied_thread(payload.text, payload.subject):
        event = EmailEvent(
            matter_id=matter_id,
            thread_id=parsed.thread_id,
            message_id=parsed.message_id,
            in_reply_to=parsed.in_reply_to,
            sender=parsed.sender,
            recipients=parsed.recipients,
            cc=parsed.cc,
            bcc=parsed.bcc,
            subject=parsed.subject,
            original_timestamp=parsed.original_timestamp,
            normalized_timestamp=parsed.normalized_timestamp,
            detected_timezone=parsed.detected_timezone,
            raw_body=parsed.raw_body,
            normalized_body=parsed.normalized_body,
            quoted_text=parsed.quoted_text,
            attachments=parsed.attachments,
            legal_event_tags=parsed.legal_event_tags,
            duplicate_quote_warning=parsed.duplicate_quote_warning,
        )
        db.add(event)
        created.append(event)
    db.commit()
    for event in created:
        db.refresh(event)
    return created

