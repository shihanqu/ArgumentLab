import type {
  AgentRouting,
  BenchmarkPacket,
  DocumentRecord,
  EmailEvent,
  JudgePersona,
  Matter,
  Provider,
  Simulation,
  SimulationConfig
} from "./types";

export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      ...(init?.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...init?.headers
    }
  });
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed: ${response.status}`);
  }
  if (response.status === 204) {
    return undefined as T;
  }
  return response.json() as Promise<T>;
}

export const api = {
  health: () => request<Record<string, unknown>>("/health"),
  matters: () => request<Matter[]>("/matters"),
  createMatter: (payload: { name: string; description?: string }) =>
    request<Matter>("/matters", { method: "POST", body: JSON.stringify(payload) }),
  deleteMatter: (matterId: string) => request<void>(`/matters/${matterId}`, { method: "DELETE" }),
  documents: (matterId: string) => request<DocumentRecord[]>(`/matters/${matterId}/documents`),
  uploadDocuments: (matterId: string, form: FormData) =>
    request<DocumentRecord[]>(`/matters/${matterId}/documents`, { method: "POST", body: form }),
  patchDocument: (matterId: string, documentId: string, document_type: string) =>
    request<DocumentRecord>(`/matters/${matterId}/documents/${documentId}`, {
      method: "PATCH",
      body: JSON.stringify({ document_type })
    }),
  emails: (matterId: string) => request<EmailEvent[]>(`/matters/${matterId}/emails`),
  ingestCopiedThread: (matterId: string, payload: { subject?: string; text: string }) =>
    request<EmailEvent[]>(`/matters/${matterId}/emails/copied-thread`, {
      method: "POST",
      body: JSON.stringify(payload)
    }),
  providers: () => request<Provider[]>("/model-routing/providers"),
  createProvider: (payload: Partial<Provider> & { api_key?: string | null }) =>
    request<Provider>("/model-routing/providers", { method: "POST", body: JSON.stringify(payload) }),
  updateProvider: (providerId: string, payload: Partial<Provider> & { api_key?: string | null }) =>
    request<Provider>(`/model-routing/providers/${providerId}`, { method: "PUT", body: JSON.stringify(payload) }),
  deleteProvider: (providerId: string) => request<void>(`/model-routing/providers/${providerId}`, { method: "DELETE" }),
  diagnostic: (providerId: string, kind: "connection" | "completion" | "structured_output") =>
    request<Record<string, unknown>>(`/model-routing/providers/${providerId}/diagnostics`, {
      method: "POST",
      body: JSON.stringify({ kind })
    }),
  agentRouting: () => request<AgentRouting[]>("/model-routing/agents"),
  updateAgentRouting: (agentId: string, payload: Partial<AgentRouting>) =>
    request<AgentRouting>(`/model-routing/agents/${agentId}`, { method: "PUT", body: JSON.stringify(payload) }),
  judgePersonas: () => request<JudgePersona[]>("/model-routing/judge-personas"),
  simulations: (matterId: string) => request<Simulation[]>(`/matters/${matterId}/simulations`),
  createSimulation: (matterId: string, config: SimulationConfig) =>
    request<Simulation>(`/matters/${matterId}/simulations`, {
      method: "POST",
      body: JSON.stringify({ config })
    }),
  simulation: (simulationId: string) => request<Simulation>(`/simulations/${simulationId}`),
  exportSimulation: (simulationId: string) =>
    request<{ storage_path: string; content?: string }>(`/simulations/${simulationId}/export`, { method: "POST" }),
  benchmarkPackets: () => request<BenchmarkPacket[]>("/benchmarks/packets"),
  runBenchmark: (packet_id: string) =>
    request<Record<string, unknown>>("/benchmarks/run", { method: "POST", body: JSON.stringify({ packet_id }) })
};

export function defaultSimulationConfig(): SimulationConfig {
  return {
    simulation_type: "motion_stress_test",
    client_side: "plaintiff",
    opponent_side: "defendant",
    procedural_posture: "motion_to_dismiss",
    jurisdiction: "New York",
    strict_record_mode: true,
    authority_mode: "uploaded_only",
    self_play: {
      mode: "standard",
      round_count: 3,
      allow_rebuttal: true,
      allow_judge_interventions: true,
      preserve_disagreement: true
    },
    judge_panel: ["strict_proceduralist", "pragmatic_trial_judge", "skeptical_appellate_judge"],
    model_routing: {},
    fallback_behavior: "mock_on_error",
    token_cap: 60000,
    cost_cap: 10,
    document_ids: [],
    email_thread_ids: []
  };
}

