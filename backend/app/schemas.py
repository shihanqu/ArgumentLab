from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


DocumentType = Literal[
    "pleading",
    "motion",
    "opposition",
    "reply",
    "exhibit",
    "contract",
    "transcript",
    "email",
    "authority",
    "correspondence",
    "other",
]

ProviderType = Literal[
    "openai_oauth",
    "openai_api_key",
    "anthropic",
    "litellm_proxy",
    "local_openai_compatible",
    "mock",
]

AuthMethod = Literal["none", "oauth_pkce", "api_key", "bearer_token", "dummy"]
Confidence = Literal["low", "medium", "high"]
Severity = Literal["low", "medium", "high", "critical"]


class MatterCreate(BaseModel):
    name: str = Field(min_length=1, max_length=240)
    description: str | None = None


class MatterRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime


class MatterSummary(MatterRead):
    document_count: int
    email_count: int
    simulation_count: int


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    matter_id: str
    filename: str
    document_type: DocumentType
    status: str
    mime_type: str | None = None
    size_bytes: int
    extracted_text: str | None = None
    classification_reason: str | None = None
    source_refs: list[dict[str, Any]] = []
    created_at: datetime


class DocumentPatch(BaseModel):
    document_type: DocumentType


class EmailEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    matter_id: str
    document_id: str | None = None
    thread_id: str
    message_id: str | None = None
    in_reply_to: str | None = None
    sender: str | None = None
    recipients: list[str] = []
    cc: list[str] = []
    bcc: list[str] = []
    subject: str | None = None
    original_timestamp: str | None = None
    normalized_timestamp: datetime | None = None
    detected_timezone: str | None = None
    raw_body: str | None = None
    normalized_body: str | None = None
    quoted_text: str | None = None
    attachments: list[dict[str, Any]] = []
    legal_event_tags: list[str] = []
    duplicate_quote_warning: bool = False
    created_at: datetime


class CopiedEmailThread(BaseModel):
    subject: str | None = None
    text: str = Field(min_length=1)


class ProviderCreate(BaseModel):
    display_name: str
    provider_type: ProviderType
    base_url: str | None = None
    model_name: str
    auth_method: AuthMethod = "none"
    api_key: str | None = None
    token_reference: str | None = None
    context_window: int | None = None
    supports_structured_output: bool | None = None
    supports_tool_calling: bool | None = None
    max_cost_per_run: float | None = None
    enabled: bool = True


class ProviderUpdate(ProviderCreate):
    pass


class ProviderRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    display_name: str
    provider_type: ProviderType
    base_url: str | None = None
    model_name: str
    auth_method: AuthMethod
    token_reference: str | None = None
    context_window: int | None = None
    supports_structured_output: bool | None = None
    supports_tool_calling: bool | None = None
    max_cost_per_run: float | None = None
    enabled: bool
    last_error: str | None = None
    diagnostics: dict[str, Any] = {}
    created_at: datetime
    updated_at: datetime
    has_secret: bool = False


class AgentRoutingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    agent_id: str
    agent_name: str
    default_provider_id: str | None = None
    fallback_provider_id: str | None = None
    temperature: float
    max_tokens: int
    strict_json: bool
    enabled: bool


class AgentRoutingUpdate(BaseModel):
    default_provider_id: str | None = None
    fallback_provider_id: str | None = None
    temperature: float = 0.2
    max_tokens: int = 1600
    strict_json: bool = True
    enabled: bool = True


class DiagnosticRequest(BaseModel):
    kind: Literal["connection", "completion", "structured_output"]


class DiagnosticResult(BaseModel):
    ok: bool
    kind: str
    message: str
    response_preview: str | None = None
    supports_json_schema: bool | None = None
    estimated_context_window: int | None = None
    last_error: str | None = None


class SelfPlayConfig(BaseModel):
    mode: Literal["quick", "standard", "deep", "custom"] = "standard"
    round_count: int = Field(default=3, ge=1, le=10)
    allow_rebuttal: bool = True
    allow_judge_interventions: bool = True
    preserve_disagreement: bool = True


class SimulationConfig(BaseModel):
    simulation_type: str = "motion_stress_test"
    client_side: str = "plaintiff"
    opponent_side: str = "defendant"
    procedural_posture: str = "motion_to_dismiss"
    jurisdiction: str = "New York"
    strict_record_mode: bool = True
    authority_mode: Literal["uploaded_only", "external_research_disabled"] = "uploaded_only"
    self_play: SelfPlayConfig = Field(default_factory=SelfPlayConfig)
    judge_panel: list[str] = Field(default_factory=lambda: ["strict_proceduralist", "pragmatic_trial_judge", "skeptical_appellate_judge"])
    custom_judge_persona: str | None = None
    model_routing: dict[str, str | None] = Field(default_factory=dict)
    fallback_behavior: Literal["use_fallback", "mock_on_error", "fail_run"] = "mock_on_error"
    token_cap: int | None = None
    cost_cap: float | None = None
    document_ids: list[str] = Field(default_factory=list)
    email_thread_ids: list[str] = Field(default_factory=list)


class SimulationRunCreate(BaseModel):
    config: SimulationConfig = Field(default_factory=SimulationConfig)


class SimulationRoundRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    simulation_id: str
    round_number: int
    title: str
    protocol: list[str]
    created_at: datetime


class SimulationTurnRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    simulation_id: str
    round_number: int
    turn_number: int
    agent_id: str
    agent_role: str
    model_provider: str | None = None
    model_name: str | None = None
    input_refs: list[dict[str, Any]] = []
    output: dict[str, Any] = {}
    claims_made: list[dict[str, Any]] = []
    claims_attacked: list[dict[str, Any]] = []
    sources_cited: list[dict[str, Any]] = []
    new_findings: list[dict[str, Any]] = []
    confidence: Confidence
    created_at: datetime


class SupportingSource(BaseModel):
    source_type: Literal["document", "email", "authority"]
    source_id: str
    page: int | None = None
    timestamp: str | None = None
    quote: str


class FindingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    simulation_id: str
    round_number: int
    source_agent: str
    severity: Severity
    confidence: Confidence
    category: str
    title: str
    description: str
    why_it_matters: str
    supporting_sources: list[dict[str, Any]]
    attacked_argument_id: str | None = None
    recommended_fix: str


class JudgeEvaluationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    simulation_id: str
    round_number: int
    persona_id: str
    persona: str
    output: dict[str, Any]
    confidence: Confidence
    created_at: datetime


class SimulationRunRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    matter_id: str
    status: str
    simulation_type: str
    config: dict[str, Any]
    summary: dict[str, Any]
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime


class SimulationDetail(SimulationRunRead):
    rounds: list[SimulationRoundRead] = []
    turns: list[SimulationTurnRead] = []
    findings: list[FindingRead] = []
    judge_evaluations: list[JudgeEvaluationRead] = []


class ExportRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    simulation_id: str
    matter_id: str
    export_type: str
    storage_path: str
    created_at: datetime
    content: str | None = None


class JudgePersonaRead(BaseModel):
    id: str
    name: str
    focus: list[str]
    default_selected: bool = False


class BenchmarkPacketRead(BaseModel):
    id: str
    name: str
    planted_issues: list[str]
    description: str


class BenchmarkRunRequest(BaseModel):
    packet_id: str


class BenchmarkRunResult(BaseModel):
    packet_id: str
    matter_id: str
    simulation_id: str
    metrics: dict[str, Any]

