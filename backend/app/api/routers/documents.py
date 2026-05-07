from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Document, EmailEvent, Matter
from app.schemas import DocumentPatch, DocumentRead, DocumentType
from app.services.email_parser import parse_email_file
from app.services.ingestion import classify_document, create_source_refs, extract_text
from app.services.workspace import matter_upload_dir, safe_filename

router = APIRouter(prefix="/matters/{matter_id}/documents", tags=["documents"])


@router.get("", response_model=list[DocumentRead])
def list_documents(matter_id: str, db: Session = Depends(get_db)) -> list[Document]:
    return list(db.scalars(select(Document).where(Document.matter_id == matter_id).order_by(Document.created_at.desc())).all())


@router.post("", response_model=list[DocumentRead])
async def upload_documents(
    matter_id: str,
    files: Annotated[list[UploadFile], File()],
    document_type: Annotated[DocumentType | None, Form()] = None,
    db: Session = Depends(get_db),
) -> list[Document]:
    matter = db.get(Matter, matter_id)
    if not matter:
        raise HTTPException(status_code=404, detail="Matter not found")

    created: list[Document] = []
    upload_dir = matter_upload_dir(matter_id)
    for upload in files:
        filename = safe_filename(upload.filename or "upload.bin")
        doc_id_prefix = safe_filename(Path(filename).stem)[:40]
        storage_path = upload_dir / f"{doc_id_prefix}_{filename}"
        content = await upload.read()
        storage_path.write_bytes(content)
        text = extract_text(storage_path, upload.content_type, filename)
        inferred_type, reason = classify_document(filename, text)
        doc = Document(
            matter_id=matter_id,
            filename=filename,
            document_type=document_type or inferred_type,
            status="extracted",
            mime_type=upload.content_type,
            storage_path=str(storage_path),
            size_bytes=len(content),
            extracted_text=text,
            classification_reason="Manual classification." if document_type else reason,
            source_refs=create_source_refs(text),
        )
        db.add(doc)
        db.flush()
        if doc.document_type == "email" or storage_path.suffix.lower() in {".eml", ".mbox", ".txt", ".html", ".htm"} and looks_like_email(text):
            for parsed in parse_email_file(storage_path, filename):
                db.add(
                    EmailEvent(
                        matter_id=matter_id,
                        document_id=doc.id,
                        raw_email_id=parsed.message_id,
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
                )
        created.append(doc)
    db.commit()
    for doc in created:
        db.refresh(doc)
    return created


@router.get("/{document_id}", response_model=DocumentRead)
def get_document(matter_id: str, document_id: str, db: Session = Depends(get_db)) -> Document:
    doc = db.get(Document, document_id)
    if not doc or doc.matter_id != matter_id:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc


@router.patch("/{document_id}", response_model=DocumentRead)
def patch_document(matter_id: str, document_id: str, payload: DocumentPatch, db: Session = Depends(get_db)) -> Document:
    doc = db.get(Document, document_id)
    if not doc or doc.matter_id != matter_id:
        raise HTTPException(status_code=404, detail="Document not found")
    doc.document_type = payload.document_type
    doc.classification_reason = "Manual classification."
    db.commit()
    db.refresh(doc)
    return doc


def looks_like_email(text: str) -> bool:
    lower = text[:3000].lower()
    return ("from:" in lower and "to:" in lower and ("subject:" in lower or "sent:" in lower or "date:" in lower))

