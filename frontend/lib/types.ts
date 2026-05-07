export type Matter = {
  id: string;
  name: string;
  description?: string | null;
  document_count: number;
  email_count: number;
  simulation_count: number;
  created_at: string;
  updated_at: string;
};

export type DocumentRecord = {
  id: string;
  matter_id: string;
  filename: string;
  document_type: string;
  status: string;
  mime_type?: string | null;
  size_bytes: number;
  extracted_text?: string | null;
  classification_reason?: string | null;
  source_refs: Array<Record<string, unknown>>;
  created_at: string;
};

export type EmailEvent = {
  id: string;
  matter_id: string;
  document_id?: string | null;
  thread_id: string;
  message_id?: string | null;
  in_reply_to?: string | null;
  sender?: string | null;
  recipients: string[];
  cc: string[];
  bcc: string[];
  subject?: string | null;
  original_timestamp?: string | null;
  normalized_timestamp?: string | null;
  detected_timezone?: string | null;
  raw_body?: string | null;
  normalized_body?: string | null;
  quoted_text?: string | null;
  attachments: Array<Record<string, unknown>>;
  legal_event_tags: string[];
  duplicate_quote_warning: boolean;
  created_at: string;
};

export type Provider = {
  id: string;
  display_name: string;
  provider_type: string;
  base_url?: string | null;
  model_name: string;
  auth_method: string;
  token_reference?: string | null;
  context_window?: number | null;
  supports_structured_output?: boolean | null;
  supports_tool_calling?: boolean | null;
  max_cost_per_run?: number | null;
  enabled: boolean;
  last_error?: string | null;
  diagnostics: Record<string, unknown>;
  has_secret: boolean;
};

export type AgentRouting = {
  agent_id: string;
  agent_name: string;
  default_provider_id?: string | null;
  fallback_provider_id?: string | null;
  temperature: number;
  max_tokens: number;
  strict_json: boolean;
  enabled: boolean;
};

export type JudgePersona = {
  id: string;
  name: string;
  focus: string[];
  default_selected: boolean;
};

export type SimulationConfig = {
  simulation_type: string;
  client_side: string;
  opponent_side: string;
  procedural_posture: string;
  jurisdiction: string;
  strict_record_mode: boolean;
  authority_mode: string;
  self_play: {
    mode: "quick" | "standard" | "deep" | "custom";
    round_count: number;
    allow_rebuttal: boolean;
    allow_judge_interventions: boolean;
    preserve_disagreement: boolean;
  };
  judge_panel: string[];
  custom_judge_persona?: string | null;
  model_routing: Record<string, string | null>;
  fallback_behavior: "use_fallback" | "mock_on_error" | "fail_run";
  token_cap?: number | null;
  cost_cap?: number | null;
  document_ids: string[];
  email_thread_ids: string[];
};

export type SimulationTurn = {
  id: string;
  simulation_id: string;
  round_number: number;
  turn_number: number;
  agent_id: string;
  agent_role: string;
  model_provider?: string | null;
  model_name?: string | null;
  input_refs: Array<Record<string, unknown>>;
  output: Record<string, unknown>;
  claims_made: Array<Record<string, unknown>>;
  claims_attacked: Array<Record<string, unknown>>;
  sources_cited: Array<Record<string, unknown>>;
  new_findings: Array<Record<string, unknown>>;
  confidence: string;
  created_at: string;
};

export type Finding = {
  id: string;
  simulation_id: string;
  round_number: number;
  source_agent: string;
  severity: string;
  confidence: string;
  category: string;
  title: string;
  description: string;
  why_it_matters: string;
  supporting_sources: Array<Record<string, unknown>>;
  recommended_fix: string;
};

export type JudgeEvaluation = {
  id: string;
  simulation_id: string;
  round_number: number;
  persona_id: string;
  persona: string;
  output: Record<string, unknown>;
  confidence: string;
  created_at: string;
};

export type Simulation = {
  id: string;
  matter_id: string;
  status: string;
  simulation_type: string;
  config: SimulationConfig;
  summary: Record<string, unknown>;
  started_at?: string | null;
  completed_at?: string | null;
  created_at: string;
  rounds: Array<Record<string, unknown>>;
  turns: SimulationTurn[];
  findings: Finding[];
  judge_evaluations: JudgeEvaluation[];
};

export type BenchmarkPacket = {
  id: string;
  name: string;
  planted_issues: string[];
  description: string;
};

