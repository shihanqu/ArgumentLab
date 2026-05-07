from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


class Matter(Base):
    __tablename__ = "matters"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("matter"))
    name: Mapped[str] = mapped_column(String(240), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    documents: Mapped[list["Document"]] = relationship(back_populates="matter", cascade="all, delete-orphan")
    emails: Mapped[list["EmailEvent"]] = relationship(back_populates="matter", cascade="all, delete-orphan")
    simulations: Mapped[list["SimulationRun"]] = relationship(back_populates="matter", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("doc"))
    matter_id: Mapped[str] = mapped_column(ForeignKey("matters.id", ondelete="CASCADE"), nullable=False)
    filename: Mapped[str] = mapped_column(String(512), nullable=False)
    document_type: Mapped[str] = mapped_column(String(64), default="other", nullable=False)
    status: Mapped[str] = mapped_column(String(64), default="uploaded", nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(200))
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    extracted_text: Mapped[str | None] = mapped_column(Text)
    classification_reason: Mapped[str | None] = mapped_column(Text)
    source_refs: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    matter: Mapped[Matter] = relationship(back_populates="documents")


class EmailEvent(Base):
    __tablename__ = "email_events"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("email"))
    matter_id: Mapped[str] = mapped_column(ForeignKey("matters.id", ondelete="CASCADE"), nullable=False)
    document_id: Mapped[str | None] = mapped_column(ForeignKey("documents.id", ondelete="SET NULL"))
    raw_email_id: Mapped[str | None] = mapped_column(String(255))
    thread_id: Mapped[str] = mapped_column(String(255), index=True)
    message_id: Mapped[str | None] = mapped_column(String(255))
    in_reply_to: Mapped[str | None] = mapped_column(String(255))
    sender: Mapped[str | None] = mapped_column(String(512))
    recipients: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    cc: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    bcc: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    subject: Mapped[str | None] = mapped_column(String(512))
    original_timestamp: Mapped[str | None] = mapped_column(String(255))
    normalized_timestamp: Mapped[datetime | None] = mapped_column(DateTime, index=True)
    detected_timezone: Mapped[str | None] = mapped_column(String(80))
    raw_body: Mapped[str | None] = mapped_column(Text)
    normalized_body: Mapped[str | None] = mapped_column(Text)
    quoted_text: Mapped[str | None] = mapped_column(Text)
    attachments: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    legal_event_tags: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    duplicate_quote_warning: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    matter: Mapped[Matter] = relationship(back_populates="emails")


class Provider(Base):
    __tablename__ = "providers"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("provider"))
    display_name: Mapped[str] = mapped_column(String(200), nullable=False)
    provider_type: Mapped[str] = mapped_column(String(80), nullable=False)
    base_url: Mapped[str | None] = mapped_column(String(512))
    model_name: Mapped[str] = mapped_column(String(200), nullable=False)
    auth_method: Mapped[str] = mapped_column(String(80), default="none", nullable=False)
    api_key: Mapped[str | None] = mapped_column(Text)
    token_reference: Mapped[str | None] = mapped_column(String(255))
    context_window: Mapped[int | None] = mapped_column(Integer)
    supports_structured_output: Mapped[bool | None] = mapped_column(Boolean)
    supports_tool_calling: Mapped[bool | None] = mapped_column(Boolean)
    max_cost_per_run: Mapped[float | None] = mapped_column(Float)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_error: Mapped[str | None] = mapped_column(Text)
    diagnostics: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class AgentRouting(Base):
    __tablename__ = "agent_routing"

    agent_id: Mapped[str] = mapped_column(String(120), primary_key=True)
    agent_name: Mapped[str] = mapped_column(String(200), nullable=False)
    default_provider_id: Mapped[str | None] = mapped_column(ForeignKey("providers.id", ondelete="SET NULL"))
    fallback_provider_id: Mapped[str | None] = mapped_column(ForeignKey("providers.id", ondelete="SET NULL"))
    temperature: Mapped[float] = mapped_column(Float, default=0.2, nullable=False)
    max_tokens: Mapped[int] = mapped_column(Integer, default=1600, nullable=False)
    strict_json: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class SimulationRun(Base):
    __tablename__ = "simulation_runs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("sim"))
    matter_id: Mapped[str] = mapped_column(ForeignKey("matters.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(64), default="queued", nullable=False)
    simulation_type: Mapped[str] = mapped_column(String(120), default="motion_stress_test", nullable=False)
    config: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    summary: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    matter: Mapped[Matter] = relationship(back_populates="simulations")
    rounds: Mapped[list["SimulationRound"]] = relationship(back_populates="simulation", cascade="all, delete-orphan")
    turns: Mapped[list["SimulationTurn"]] = relationship(back_populates="simulation", cascade="all, delete-orphan")
    findings: Mapped[list["SimulationFinding"]] = relationship(back_populates="simulation", cascade="all, delete-orphan")
    judge_evaluations: Mapped[list["JudgeEvaluation"]] = relationship(back_populates="simulation", cascade="all, delete-orphan")


class SimulationRound(Base):
    __tablename__ = "simulation_rounds"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("round"))
    simulation_id: Mapped[str] = mapped_column(ForeignKey("simulation_runs.id", ondelete="CASCADE"), nullable=False)
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    protocol: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    simulation: Mapped[SimulationRun] = relationship(back_populates="rounds")


class SimulationTurn(Base):
    __tablename__ = "simulation_turns"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("turn"))
    simulation_id: Mapped[str] = mapped_column(ForeignKey("simulation_runs.id", ondelete="CASCADE"), nullable=False)
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    turn_number: Mapped[int] = mapped_column(Integer, nullable=False)
    agent_id: Mapped[str] = mapped_column(String(120), nullable=False)
    agent_role: Mapped[str] = mapped_column(String(120), nullable=False)
    model_provider: Mapped[str | None] = mapped_column(String(120))
    model_name: Mapped[str | None] = mapped_column(String(200))
    input_refs: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    output: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    claims_made: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    claims_attacked: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    sources_cited: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    new_findings: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    confidence: Mapped[str] = mapped_column(String(32), default="medium", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    simulation: Mapped[SimulationRun] = relationship(back_populates="turns")


class SimulationFinding(Base):
    __tablename__ = "simulation_findings"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("finding"))
    simulation_id: Mapped[str] = mapped_column(ForeignKey("simulation_runs.id", ondelete="CASCADE"), nullable=False)
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    source_agent: Mapped[str] = mapped_column(String(120), nullable=False)
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    confidence: Mapped[str] = mapped_column(String(32), nullable=False)
    category: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(String(240), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    why_it_matters: Mapped[str] = mapped_column(Text, nullable=False)
    supporting_sources: Mapped[list[dict]] = mapped_column(JSON, default=list, nullable=False)
    attacked_argument_id: Mapped[str | None] = mapped_column(String(120))
    recommended_fix: Mapped[str] = mapped_column(Text, nullable=False)

    simulation: Mapped[SimulationRun] = relationship(back_populates="findings")


class JudgeEvaluation(Base):
    __tablename__ = "simulation_judge_evaluations"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("judge_eval"))
    simulation_id: Mapped[str] = mapped_column(ForeignKey("simulation_runs.id", ondelete="CASCADE"), nullable=False)
    round_number: Mapped[int] = mapped_column(Integer, nullable=False)
    persona_id: Mapped[str] = mapped_column(String(120), nullable=False)
    persona: Mapped[str] = mapped_column(String(200), nullable=False)
    output: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    confidence: Mapped[str] = mapped_column(String(32), default="medium", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    simulation: Mapped[SimulationRun] = relationship(back_populates="judge_evaluations")


class SimulationDisagreement(Base):
    __tablename__ = "simulation_disagreements"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("disagreement"))
    simulation_id: Mapped[str] = mapped_column(ForeignKey("simulation_runs.id", ondelete="CASCADE"), nullable=False)
    disagreement_type: Mapped[str] = mapped_column(String(80), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    agents: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class SimulationSourceLink(Base):
    __tablename__ = "simulation_source_links"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("source_link"))
    simulation_id: Mapped[str] = mapped_column(ForeignKey("simulation_runs.id", ondelete="CASCADE"), nullable=False)
    turn_id: Mapped[str | None] = mapped_column(ForeignKey("simulation_turns.id", ondelete="CASCADE"))
    finding_id: Mapped[str | None] = mapped_column(ForeignKey("simulation_findings.id", ondelete="CASCADE"))
    source_type: Mapped[str] = mapped_column(String(80), nullable=False)
    source_id: Mapped[str] = mapped_column(String(120), nullable=False)
    locator: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    quote: Mapped[str | None] = mapped_column(Text)


class Export(Base):
    __tablename__ = "exports"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: new_id("export"))
    simulation_id: Mapped[str] = mapped_column(ForeignKey("simulation_runs.id", ondelete="CASCADE"), nullable=False)
    matter_id: Mapped[str] = mapped_column(ForeignKey("matters.id", ondelete="CASCADE"), nullable=False)
    export_type: Mapped[str] = mapped_column(String(80), default="markdown", nullable=False)
    storage_path: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

