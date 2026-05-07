"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { PlugZap, Plus, Trash2, Wand2 } from "lucide-react";
import { useMemo, useState } from "react";
import { api } from "@/lib/api";
import type { AgentRouting, Provider } from "@/lib/types";
import { Button } from "./ui/button";
import { Checkbox, Input, Label, Select } from "./ui/field";

const providerTypes = [
  ["openai_oauth", "OpenAI OAuth"],
  ["openai_api_key", "OpenAI API key"],
  ["anthropic", "Anthropic"],
  ["litellm_proxy", "LiteLLM Proxy"],
  ["local_openai_compatible", "Local OpenAI-compatible"],
  ["mock", "Mock provider"]
];

const authMethods = ["none", "oauth_pkce", "api_key", "bearer_token", "dummy"];

const blankProvider = {
  display_name: "Local OpenAI-compatible",
  provider_type: "local_openai_compatible",
  base_url: "http://localhost:8000",
  model_name: "local-model",
  auth_method: "dummy",
  api_key: "",
  token_reference: "",
  context_window: 32768,
  supports_structured_output: false,
  supports_tool_calling: false,
  max_cost_per_run: 5,
  enabled: true
};

export function ModelRouting() {
  const qc = useQueryClient();
  const providers = useQuery({ queryKey: ["providers"], queryFn: api.providers });
  const routes = useQuery({ queryKey: ["agent-routing"], queryFn: api.agentRouting });
  const [editing, setEditing] = useState<Partial<Provider> & { api_key?: string | null }>(blankProvider);
  const [diagnostic, setDiagnostic] = useState<Record<string, unknown> | null>(null);

  const saveProvider = useMutation({
    mutationFn: () => (editing.id ? api.updateProvider(editing.id, normalizeProviderPayload(editing)) : api.createProvider(normalizeProviderPayload(editing))),
    onSuccess: async () => {
      setEditing(blankProvider);
      await qc.invalidateQueries({ queryKey: ["providers"] });
    }
  });
  const deleteProvider = useMutation({
    mutationFn: (providerId: string) => api.deleteProvider(providerId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["providers"] })
  });
  const runDiagnostic = useMutation({
    mutationFn: ({ providerId, kind }: { providerId: string; kind: "connection" | "completion" | "structured_output" }) => api.diagnostic(providerId, kind),
    onSuccess: (result) => {
      setDiagnostic(result);
      qc.invalidateQueries({ queryKey: ["providers"] });
    }
  });

  return (
    <div className="space-y-4">
      <section className="rounded-md border border-line bg-panel p-5 shadow-warroom">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold">Settings → Model Routing</h2>
            <p className="mt-1 text-sm text-sage">Visible provider registry, agent assignments, run diagnostics, and local LLM routing.</p>
          </div>
          <Button variant="secondary" onClick={() => setEditing(blankProvider)}>
            <Plus size={16} />
            New Provider
          </Button>
        </div>
      </section>
      <div className="grid grid-cols-[420px_1fr] gap-4">
        <section className="rounded-md border border-line bg-panel p-5 shadow-warroom">
          <h3 className="font-semibold">Provider Registry</h3>
          <div className="mt-4 grid grid-cols-2 gap-3">
            <Field label="Display name">
              <Input value={editing.display_name ?? ""} onChange={(event) => setEditing({ ...editing, display_name: event.target.value })} />
            </Field>
            <Field label="Provider type">
              <Select value={editing.provider_type ?? "mock"} onChange={(event) => setEditing({ ...editing, provider_type: event.target.value })}>
                {providerTypes.map(([value, label]) => (
                  <option key={value} value={value}>
                    {label}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="Base URL">
              <Input value={editing.base_url ?? ""} onChange={(event) => setEditing({ ...editing, base_url: event.target.value })} placeholder="http://localhost:8000" />
            </Field>
            <Field label="Model name">
              <Input value={editing.model_name ?? ""} onChange={(event) => setEditing({ ...editing, model_name: event.target.value })} />
            </Field>
            <Field label="Auth method">
              <Select value={editing.auth_method ?? "none"} onChange={(event) => setEditing({ ...editing, auth_method: event.target.value })}>
                {authMethods.map((method) => (
                  <option key={method} value={method}>
                    {method}
                  </option>
                ))}
              </Select>
            </Field>
            <Field label="API key / token">
              <Input
                type="password"
                value={editing.api_key ?? ""}
                onChange={(event) => setEditing({ ...editing, api_key: event.target.value })}
                placeholder={editing.has_secret ? "Secret already stored" : "Optional"}
              />
            </Field>
            <Field label="Token reference">
              <Input value={editing.token_reference ?? ""} onChange={(event) => setEditing({ ...editing, token_reference: event.target.value })} />
            </Field>
            <Field label="Context window">
              <Input type="number" value={editing.context_window ?? ""} onChange={(event) => setEditing({ ...editing, context_window: Number(event.target.value) })} />
            </Field>
            <Field label="Max cost / run">
              <Input type="number" value={editing.max_cost_per_run ?? ""} onChange={(event) => setEditing({ ...editing, max_cost_per_run: Number(event.target.value) })} />
            </Field>
            <div className="col-span-2 grid grid-cols-3 gap-2 rounded-md border border-line bg-white p-3">
              <Checkbox checked={Boolean(editing.supports_structured_output)} onChange={(checked) => setEditing({ ...editing, supports_structured_output: checked })} label="JSON/schema" />
              <Checkbox checked={Boolean(editing.supports_tool_calling)} onChange={(checked) => setEditing({ ...editing, supports_tool_calling: checked })} label="Tool support" />
              <Checkbox checked={editing.enabled ?? true} onChange={(checked) => setEditing({ ...editing, enabled: checked })} label="Enabled" />
            </div>
          </div>
          <Button className="mt-4 w-full" onClick={() => saveProvider.mutate()} disabled={saveProvider.isPending}>
            Save Provider
          </Button>
        </section>
        <section className="rounded-md border border-line bg-panel p-5 shadow-warroom">
          <h3 className="font-semibold">Registered Providers</h3>
          <div className="mt-4 grid gap-3">
            {(providers.data ?? []).map((provider) => (
              <article key={provider.id} className="rounded-md border border-line bg-white p-4">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <div className="font-semibold">{provider.display_name}</div>
                    <div className="mt-1 text-xs text-sage">
                      {provider.provider_type} | {provider.model_name} | {provider.base_url || "default endpoint"}
                    </div>
                    <div className="mt-2 flex flex-wrap gap-1 text-xs">
                      <Badge>Context: {provider.context_window ?? "unknown"}</Badge>
                      <Badge>JSON/schema: {flag(provider.supports_structured_output)}</Badge>
                      <Badge>Tools: {flag(provider.supports_tool_calling)}</Badge>
                      <Badge>{provider.enabled ? "Enabled" : "Disabled"}</Badge>
                    </div>
                    {provider.last_error ? <div className="mt-2 rounded-sm bg-[#f7e5df] px-2 py-1 text-xs text-risk">Last error: {provider.last_error}</div> : null}
                  </div>
                  <div className="flex gap-1">
                    <Button variant="secondary" size="icon" title="Edit provider" onClick={() => setEditing({ ...provider, api_key: "" })}>
                      <Wand2 size={15} />
                    </Button>
                    <Button variant="danger" size="icon" title="Delete provider" onClick={() => deleteProvider.mutate(provider.id)}>
                      <Trash2 size={15} />
                    </Button>
                  </div>
                </div>
                <div className="mt-3 flex flex-wrap gap-2">
                  <Button variant="secondary" size="sm" onClick={() => runDiagnostic.mutate({ providerId: provider.id, kind: "connection" })}>
                    <PlugZap size={14} />
                    Test provider connection
                  </Button>
                  <Button variant="secondary" size="sm" onClick={() => runDiagnostic.mutate({ providerId: provider.id, kind: "structured_output" })}>
                    Run sample structured output
                  </Button>
                  <Button variant="secondary" size="sm" onClick={() => runDiagnostic.mutate({ providerId: provider.id, kind: "completion" })}>
                    Run sample completion
                  </Button>
                </div>
              </article>
            ))}
          </div>
          {diagnostic ? (
            <div className="mt-4 rounded-md border border-line bg-[#f0eadc] p-3 text-sm">
              <div className="font-semibold">Latest Diagnostic</div>
              <pre className="mt-2 max-h-44 overflow-auto whitespace-pre-wrap text-xs">{JSON.stringify(diagnostic, null, 2)}</pre>
            </div>
          ) : null}
        </section>
      </div>
      <AgentRoutingTable providers={providers.data ?? []} routes={routes.data ?? []} />
    </div>
  );
}

function AgentRoutingTable({ providers, routes }: { providers: Provider[]; routes: AgentRouting[] }) {
  const qc = useQueryClient();
  const update = useMutation({
    mutationFn: ({ agentId, payload }: { agentId: string; payload: Partial<AgentRouting> }) => api.updateAgentRouting(agentId, payload),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["agent-routing"] })
  });
  const providersById = useMemo(() => Object.fromEntries(providers.map((provider) => [provider.id, provider])), [providers]);

  return (
    <section className="rounded-md border border-line bg-panel p-5 shadow-warroom">
      <h3 className="font-semibold">Agent Routing Table</h3>
      <div className="mt-4 overflow-x-auto">
        <table className="w-full min-w-[980px] border-collapse text-sm">
          <thead>
            <tr className="border-b border-line text-left text-xs uppercase tracking-wide text-sage">
              <th className="py-2">Agent</th>
              <th>Default Model</th>
              <th>Fallback Model</th>
              <th>Temperature</th>
              <th>Max Tokens</th>
              <th>Strict JSON</th>
            </tr>
          </thead>
          <tbody>
            {routes.map((route) => (
              <tr key={route.agent_id} className="border-b border-line">
                <td className="py-3 font-semibold">{route.agent_name}</td>
                <td className="pr-2">
                  <ProviderSelect
                    providers={providers}
                    value={route.default_provider_id ?? ""}
                    onChange={(value) => update.mutate({ agentId: route.agent_id, payload: { ...route, default_provider_id: value || null } })}
                  />
                  <div className="mt-1 text-xs text-sage">{route.default_provider_id ? providersById[route.default_provider_id]?.model_name : "Unassigned"}</div>
                </td>
                <td className="pr-2">
                  <ProviderSelect
                    providers={providers}
                    value={route.fallback_provider_id ?? ""}
                    onChange={(value) => update.mutate({ agentId: route.agent_id, payload: { ...route, fallback_provider_id: value || null } })}
                  />
                </td>
                <td className="pr-2">
                  <Input
                    type="number"
                    step="0.05"
                    value={route.temperature}
                    onChange={(event) => update.mutate({ agentId: route.agent_id, payload: { ...route, temperature: Number(event.target.value) } })}
                  />
                </td>
                <td className="pr-2">
                  <Input
                    type="number"
                    value={route.max_tokens}
                    onChange={(event) => update.mutate({ agentId: route.agent_id, payload: { ...route, max_tokens: Number(event.target.value) } })}
                  />
                </td>
                <td>
                  <Checkbox checked={route.strict_json} onChange={(checked) => update.mutate({ agentId: route.agent_id, payload: { ...route, strict_json: checked } })} label="yes/no" />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function ProviderSelect({ providers, value, onChange }: { providers: Provider[]; value: string; onChange: (value: string) => void }) {
  return (
    <Select value={value} onChange={(event) => onChange(event.target.value)}>
      <option value="">Unassigned</option>
      {providers.map((provider) => (
        <option key={provider.id} value={provider.id}>
          {provider.display_name} / {provider.model_name}
        </option>
      ))}
    </Select>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <Label>{label}</Label>
      {children}
    </div>
  );
}

function Badge({ children }: { children: React.ReactNode }) {
  return <span className="rounded-sm bg-[#eef2ef] px-2 py-1 text-sage">{children}</span>;
}

function flag(value?: boolean | null) {
  if (value === true) return "yes";
  if (value === false) return "no";
  return "unknown";
}

function normalizeProviderPayload(editing: Partial<Provider> & { api_key?: string | null }) {
  return {
    display_name: editing.display_name || "Provider",
    provider_type: editing.provider_type || "mock",
    base_url: editing.base_url || null,
    model_name: editing.model_name || "model",
    auth_method: editing.auth_method || "none",
    api_key: editing.api_key || null,
    token_reference: editing.token_reference || null,
    context_window: editing.context_window ? Number(editing.context_window) : null,
    supports_structured_output: editing.supports_structured_output ?? null,
    supports_tool_calling: editing.supports_tool_calling ?? null,
    max_cost_per_run: editing.max_cost_per_run ? Number(editing.max_cost_per_run) : null,
    enabled: editing.enabled ?? true
  };
}

