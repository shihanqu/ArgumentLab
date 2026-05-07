"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { PlayCircle } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { api, defaultSimulationConfig } from "@/lib/api";
import type { Simulation, SimulationConfig } from "@/lib/types";
import { Button } from "./ui/button";
import { Checkbox, Input, Label, Select, Textarea } from "./ui/field";

export function SimulationSetup({ matterId, onSimulationCreated }: { matterId: string; onSimulationCreated: (simulation: Simulation) => void }) {
  const qc = useQueryClient();
  const providers = useQuery({ queryKey: ["providers"], queryFn: api.providers });
  const routes = useQuery({ queryKey: ["agent-routing"], queryFn: api.agentRouting });
  const judges = useQuery({ queryKey: ["judge-personas"], queryFn: api.judgePersonas });
  const docs = useQuery({ queryKey: ["documents", matterId], queryFn: () => api.documents(matterId) });
  const emails = useQuery({ queryKey: ["emails", matterId], queryFn: () => api.emails(matterId) });
  const [config, setConfig] = useState<SimulationConfig>(defaultSimulationConfig());

  useEffect(() => {
    setConfig((current) => ({
      ...current,
      document_ids: docs.data?.map((doc) => doc.id) ?? [],
      email_thread_ids: Array.from(new Set((emails.data ?? []).map((email) => email.thread_id))),
      model_routing: Object.fromEntries((routes.data ?? []).map((route) => [route.agent_id, route.default_provider_id ?? null]))
    }));
  }, [docs.data, emails.data, routes.data]);

  const create = useMutation({
    mutationFn: () => api.createSimulation(matterId, config),
    onSuccess: async (simulation) => {
      await Promise.all([qc.invalidateQueries({ queryKey: ["simulations", matterId] }), qc.invalidateQueries({ queryKey: ["matters"] })]);
      onSimulationCreated(simulation);
    }
  });

  const providerOptions = providers.data ?? [];
  const emailThreads = useMemo(() => Array.from(new Set((emails.data ?? []).map((email) => email.thread_id))), [emails.data]);

  return (
    <div className="space-y-4">
      <section className="rounded-md border border-line bg-panel p-5 shadow-warroom">
        <h2 className="text-lg font-semibold">Simulation Setup</h2>
        <p className="mt-1 text-sm text-sage">Configure side, posture, debate depth, judge panel, strict record mode, authority limits, and run-level model overrides.</p>
      </section>
      <section className="grid grid-cols-[0.9fr_1.1fr] gap-4">
        <div className="rounded-md border border-line bg-panel p-5 shadow-warroom">
          <h3 className="font-semibold">Run Configuration</h3>
          <div className="mt-4 grid grid-cols-2 gap-3">
            <Field label="Client side">
              <Input value={config.client_side} onChange={(event) => update(config, setConfig, { client_side: event.target.value })} />
            </Field>
            <Field label="Opponent side">
              <Input value={config.opponent_side} onChange={(event) => update(config, setConfig, { opponent_side: event.target.value })} />
            </Field>
            <Field label="Procedural posture">
              <Select value={config.procedural_posture} onChange={(event) => update(config, setConfig, { procedural_posture: event.target.value })}>
                <option value="motion_to_dismiss">Motion to dismiss</option>
                <option value="summary_judgment">Summary judgment</option>
                <option value="preliminary_injunction">Preliminary injunction</option>
                <option value="discovery_dispute">Discovery dispute</option>
                <option value="trial_brief">Trial brief</option>
              </Select>
            </Field>
            <Field label="Jurisdiction">
              <Input value={config.jurisdiction} onChange={(event) => update(config, setConfig, { jurisdiction: event.target.value })} />
            </Field>
            <Field label="Self-play depth">
              <Select
                value={config.self_play.mode}
                onChange={(event) => {
                  const mode = event.target.value as SimulationConfig["self_play"]["mode"];
                  const counts = { quick: 1, standard: 3, deep: 6, custom: config.self_play.round_count };
                  update(config, setConfig, { self_play: { ...config.self_play, mode, round_count: counts[mode] } });
                }}
              >
                <option value="quick">Quick: 1 round</option>
                <option value="standard">Standard: 3 rounds</option>
                <option value="deep">Deep: 5-7 rounds</option>
                <option value="custom">Custom</option>
              </Select>
            </Field>
            <Field label="Round count">
              <Input
                type="number"
                min={1}
                max={10}
                value={config.self_play.round_count}
                onChange={(event) => update(config, setConfig, { self_play: { ...config.self_play, mode: "custom", round_count: Number(event.target.value) } })}
              />
            </Field>
          </div>
          <div className="mt-4 grid grid-cols-2 gap-3 rounded-md border border-line bg-white p-3">
            <Checkbox checked={config.strict_record_mode} onChange={(checked) => update(config, setConfig, { strict_record_mode: checked })} label="Strict record mode" />
            <Checkbox checked={config.self_play.allow_judge_interventions} onChange={(checked) => update(config, setConfig, { self_play: { ...config.self_play, allow_judge_interventions: checked } })} label="Judge interventions" />
            <Checkbox checked={config.self_play.allow_rebuttal} onChange={(checked) => update(config, setConfig, { self_play: { ...config.self_play, allow_rebuttal: checked } })} label="Allow rebuttal" />
            <Checkbox checked={config.self_play.preserve_disagreement} onChange={(checked) => update(config, setConfig, { self_play: { ...config.self_play, preserve_disagreement: checked } })} label="Preserve disagreement" />
          </div>
          <div className="mt-4 grid grid-cols-2 gap-3">
            <Field label="Fallback behavior">
              <Select value={config.fallback_behavior} onChange={(event) => update(config, setConfig, { fallback_behavior: event.target.value as SimulationConfig["fallback_behavior"] })}>
                <option value="mock_on_error">Mock on error</option>
                <option value="use_fallback">Use fallback</option>
                <option value="fail_run">Fail run</option>
              </Select>
            </Field>
            <Field label="Authority mode">
              <Select value={config.authority_mode} onChange={(event) => update(config, setConfig, { authority_mode: event.target.value })}>
                <option value="uploaded_only">Uploaded only</option>
                <option value="external_research_disabled">External research disabled</option>
              </Select>
            </Field>
          </div>
        </div>
        <div className="rounded-md border border-line bg-panel p-5 shadow-warroom">
          <h3 className="font-semibold">Judge Panel and Run-Level Overrides</h3>
          <div className="mt-4 grid grid-cols-2 gap-3">
            {(judges.data ?? []).map((judge) => (
              <label key={judge.id} className="rounded-md border border-line bg-white p-3 text-sm">
                <div className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    checked={config.judge_panel.includes(judge.id)}
                    onChange={(event) => {
                      const next = event.target.checked ? [...config.judge_panel, judge.id] : config.judge_panel.filter((id) => id !== judge.id);
                      update(config, setConfig, { judge_panel: next });
                    }}
                    className="h-4 w-4 accent-docket"
                  />
                  <span className="font-semibold">{judge.name}</span>
                </div>
                <div className="mt-2 text-xs leading-5 text-sage">{judge.focus.slice(0, 4).join(", ")}</div>
              </label>
            ))}
          </div>
          <div className="mt-4">
            <Label>Custom persona text</Label>
            <Textarea value={config.custom_judge_persona ?? ""} onChange={(event) => update(config, setConfig, { custom_judge_persona: event.target.value })} />
          </div>
          <h4 className="mt-5 font-semibold">Model per agent</h4>
          <div className="mt-3 grid grid-cols-2 gap-3">
            {(routes.data ?? []).map((route) => (
              <Field key={route.agent_id} label={route.agent_name}>
                <Select
                  value={config.model_routing[route.agent_id] ?? ""}
                  onChange={(event) => update(config, setConfig, { model_routing: { ...config.model_routing, [route.agent_id]: event.target.value || null } })}
                >
                  <option value="">Route default</option>
                  {providerOptions.map((provider) => (
                    <option key={provider.id} value={provider.id}>
                      {provider.display_name} / {provider.model_name}
                    </option>
                  ))}
                </Select>
              </Field>
            ))}
          </div>
        </div>
      </section>
      <section className="rounded-md border border-line bg-panel p-5 shadow-warroom">
        <div className="grid grid-cols-[1fr_260px] gap-4">
          <div>
            <h3 className="font-semibold">Included Sources</h3>
            <p className="mt-1 text-sm text-sage">
              {config.document_ids.length} document(s), {emailThreads.length} email thread(s), strict record mode {config.strict_record_mode ? "enabled" : "disabled"}.
            </p>
          </div>
          <Button onClick={() => create.mutate()} disabled={create.isPending} className="h-12">
            <PlayCircle size={18} />
            Launch Self-Play
          </Button>
        </div>
      </section>
    </div>
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

function update(config: SimulationConfig, setConfig: (config: SimulationConfig) => void, patch: Partial<SimulationConfig>) {
  setConfig({ ...config, ...patch });
}

