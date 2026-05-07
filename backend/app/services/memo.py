from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Export, JudgeEvaluation, SimulationFinding, SimulationRun, SimulationTurn
from app.services.workspace import matter_export_dir


def export_vulnerability_memo(db: Session, simulation_id: str) -> Export:
    run = db.get(SimulationRun, simulation_id)
    if not run:
        raise ValueError("Simulation not found")
    findings = list(db.scalars(select(SimulationFinding).where(SimulationFinding.simulation_id == simulation_id)).all())
    turns = list(db.scalars(select(SimulationTurn).where(SimulationTurn.simulation_id == simulation_id).order_by(SimulationTurn.round_number, SimulationTurn.turn_number)).all())
    judges = list(db.scalars(select(JudgeEvaluation).where(JudgeEvaluation.simulation_id == simulation_id)).all())
    content = render_memo(run, findings, turns, judges)
    export_dir = matter_export_dir(run.matter_id)
    path = export_dir / f"{simulation_id}_vulnerability_memo.md"
    path.write_text(content)
    export = Export(simulation_id=simulation_id, matter_id=run.matter_id, export_type="markdown", storage_path=str(path))
    db.add(export)
    db.commit()
    db.refresh(export)
    return export


def render_memo(run: SimulationRun, findings: list[SimulationFinding], turns: list[SimulationTurn], judges: list[JudgeEvaluation]) -> str:
    lines = [
        "# Argument Lab Vulnerability Memo",
        "",
        f"Simulation: `{run.id}`",
        f"Status: {run.status}",
        f"Strict record mode: {run.config.get('strict_record_mode', True)}",
        f"Authority mode: {run.config.get('authority_mode', 'uploaded_only')}",
        "",
        "## Executive Vulnerabilities",
    ]
    if findings:
        for item in findings:
            lines.extend(
                [
                    f"### {item.severity.upper()}: {item.title}",
                    item.description,
                    "",
                    f"Why it matters: {item.why_it_matters}",
                    f"Confidence: {item.confidence}",
                    f"Recommended fix: {item.recommended_fix}",
                    "",
                    "Sources:",
                ]
            )
            if item.supporting_sources:
                for source in item.supporting_sources:
                    locator = source.get("timestamp") or source.get("page") or "source"
                    quote = (source.get("quote") or "").replace("\n", " ")[:500]
                    lines.append(f"- {source.get('source_type')} `{source.get('source_id')}` ({locator}): {quote}")
            else:
                lines.append("- No pinpoint source available.")
            lines.append("")
    else:
        lines.append("No structured vulnerabilities were generated.")
        lines.append("")

    lines.extend(["## Judge Persona Views", ""])
    for judge in judges:
        output = judge.output
        lines.extend(
            [
                f"### {judge.persona}",
                output.get("tentative_view", ""),
                "",
                "Top concerns:",
            ]
        )
        for concern in output.get("top_concerns", []):
            lines.append(f"- {concern}")
        lines.append("")

    lines.extend(["## Transcript Index", ""])
    for turn in turns:
        claim = turn.output.get("claim") or turn.output.get("tentative_view") or ""
        lines.append(f"- Round {turn.round_number}, Turn {turn.turn_number}, {turn.agent_role} using {turn.model_provider}/{turn.model_name}: {claim[:220]}")

    lines.extend(
        [
            "",
            "## Authority Limitation",
            "Argument Lab v0.1 checks uploaded authority support only. It does not verify whether any case, statute, or rule remains good law.",
        ]
    )
    return "\n".join(lines)

