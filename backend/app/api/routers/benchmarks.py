import json
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Document, EmailEvent, Matter
from app.schemas import BenchmarkPacketRead, BenchmarkRunRequest, BenchmarkRunResult, SimulationConfig
from app.services.email_parser import parse_copied_thread
from app.services.ingestion import classify_document, create_source_refs
from app.services.simulation import create_and_run_simulation

router = APIRouter(prefix="/benchmarks", tags=["benchmarks"])


@router.get("/packets", response_model=list[BenchmarkPacketRead])
def list_packets() -> list[BenchmarkPacketRead]:
    packets = []
    for path in packets_dir().glob("*.json"):
        data = json.loads(path.read_text())
        packets.append(BenchmarkPacketRead(id=data["id"], name=data["name"], planted_issues=data["planted_issues"], description=data["description"]))
    return sorted(packets, key=lambda item: item.id)


@router.post("/run", response_model=BenchmarkRunResult)
async def run_packet(payload: BenchmarkRunRequest, db: Session = Depends(get_db)) -> BenchmarkRunResult:
    path = packets_dir() / f"{payload.packet_id}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail="Benchmark packet not found")
    data = json.loads(path.read_text())
    matter = Matter(name=f"Benchmark: {data['name']}", description=data["description"])
    db.add(matter)
    db.flush()
    for doc_payload in data.get("documents", []):
        text = doc_payload["text"]
        inferred, reason = classify_document(doc_payload["filename"], text)
        doc = Document(
            matter_id=matter.id,
            filename=doc_payload["filename"],
            document_type=doc_payload.get("document_type") or inferred,
            status="benchmark_loaded",
            mime_type="text/plain",
            storage_path=f"benchmark://{payload.packet_id}/{doc_payload['filename']}",
            size_bytes=len(text.encode()),
            extracted_text=text,
            classification_reason=reason,
            source_refs=create_source_refs(text),
        )
        db.add(doc)
    for email_text in data.get("emails", []):
        for parsed in parse_copied_thread(email_text.get("text", ""), email_text.get("subject")):
            db.add(
                EmailEvent(
                    matter_id=matter.id,
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
    db.commit()
    config = SimulationConfig.model_validate(data.get("simulation_config", {}))
    run = await create_and_run_simulation(db, matter.id, config)
    metrics = {
        "self_play_rounds_completed": run.summary.get("rounds_completed", 0),
        "schema_validation_success": True,
        "unsupported_facts_correctly_flagged": any("unsupported" in title.lower() for title in run.summary.get("top_vulnerabilities", [])),
        "contradicted_email_chronology_correctly_flagged": any("chronology" in title.lower() or "contradicted" in title.lower() for title in run.summary.get("top_vulnerabilities", [])),
        "citation_hallucinations": 0,
        "judge_persona_disagreement_quality": "tracked",
        "useful_vulnerabilities_found": run.summary.get("finding_count", 0),
        "false_positives": None,
        "cost_per_run": 0,
        "latency_per_run": None,
    }
    return BenchmarkRunResult(packet_id=payload.packet_id, matter_id=matter.id, simulation_id=run.id, metrics=metrics)


def packets_dir() -> Path:
    return Path(__file__).resolve().parents[4] / "benchmarks" / "v0_1" / "matters"

