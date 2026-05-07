"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { Download, Scale } from "lucide-react";
import { useMemo, useState } from "react";
import { api } from "@/lib/api";
import type { Finding } from "@/lib/types";
import { Button } from "./ui/button";

const tabs = [
  "Top Vulnerabilities",
  "Opposing Arguments",
  "Judge Persona Views",
  "Unsupported Facts",
  "Email Timeline Issues",
  "Citation/Authority Issues",
  "Recommended Fixes",
  "Transcript",
  "Export"
];

export function FindingsDashboard({ matterId, selectedSimulationId }: { matterId: string; selectedSimulationId: string | null }) {
  const [tab, setTab] = useState(tabs[0]);
  const runs = useQuery({ queryKey: ["simulations", matterId], queryFn: () => api.simulations(matterId) });
  const chosenId = selectedSimulationId ?? runs.data?.[0]?.id;
  const detail = useQuery({ queryKey: ["simulation", chosenId], queryFn: () => api.simulation(chosenId as string), enabled: Boolean(chosenId) });
  const exportMemo = useMutation({ mutationFn: () => api.exportSimulation(chosenId as string) });
  const findings = detail.data?.findings ?? [];

  const filtered = useMemo(() => filterFindings(findings, tab), [findings, tab]);

  if (!chosenId) {
    return <div className="rounded-md border border-line bg-panel p-5 text-sm text-sage shadow-warroom">No findings yet. Run a simulation first.</div>;
  }

  return (
    <div className="space-y-4">
      <section className="rounded-md border border-line bg-panel p-5 shadow-warroom">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold">Findings Dashboard</h2>
            <p className="mt-1 text-sm text-sage">Structured vulnerability memo inputs, source links, judge reactions, unsupported facts, authority warnings, and transcript.</p>
          </div>
          <div className="flex items-center gap-2 rounded-sm bg-[#eef2ef] px-3 py-2 text-sm text-sage">
            <Scale size={16} />
            {findings.length} finding(s)
          </div>
        </div>
        <div className="mt-4 flex flex-wrap gap-2">
          {tabs.map((item) => (
            <button
              key={item}
              onClick={() => setTab(item)}
              className={`rounded-md border px-3 py-2 text-sm ${item === tab ? "border-ink bg-ink text-paper" : "border-line bg-white text-ink"}`}
            >
              {item}
            </button>
          ))}
        </div>
      </section>
      {tab === "Judge Persona Views" ? (
        <JudgeViews judges={detail.data?.judge_evaluations ?? []} />
      ) : tab === "Transcript" ? (
        <Transcript turns={detail.data?.turns ?? []} />
      ) : tab === "Export" ? (
        <section className="rounded-md border border-line bg-panel p-5 shadow-warroom">
          <Button onClick={() => exportMemo.mutate()} disabled={exportMemo.isPending}>
            <Download size={16} />
            Export Vulnerability Memo
          </Button>
          {exportMemo.data ? (
            <div className="mt-4">
              <div className="mb-2 text-sm text-sage">{exportMemo.data.storage_path}</div>
              <pre className="max-h-[620px] overflow-auto whitespace-pre-wrap rounded-md border border-line bg-white p-4 text-sm">{exportMemo.data.content}</pre>
            </div>
          ) : null}
        </section>
      ) : (
        <FindingList findings={filtered} />
      )}
    </div>
  );
}

function filterFindings(findings: Finding[], tab: string) {
  if (tab === "Unsupported Facts") return findings.filter((finding) => finding.category.includes("fact"));
  if (tab === "Email Timeline Issues") return findings.filter((finding) => finding.category.includes("email"));
  if (tab === "Citation/Authority Issues") return findings.filter((finding) => finding.category.includes("authority"));
  if (tab === "Recommended Fixes") return findings;
  if (tab === "Opposing Arguments") return findings.filter((finding) => ["procedural_issue", "legal_standard_issue", "contradicted_fact"].includes(finding.category));
  return findings;
}

function FindingList({ findings }: { findings: Finding[] }) {
  return (
    <section className="grid gap-3">
      {findings.map((finding) => (
        <article key={finding.id} className="rounded-md border border-line bg-panel p-5 shadow-warroom">
          <div className="flex items-start justify-between gap-4">
            <div>
              <div className="text-xs uppercase tracking-wide text-sage">
                Round {finding.round_number} | {finding.source_agent} | {finding.category}
              </div>
              <h3 className="mt-1 text-lg font-semibold">{finding.title}</h3>
            </div>
            <span className={`rounded-sm px-2 py-1 text-xs ${finding.severity === "critical" || finding.severity === "high" ? "bg-[#f7e5df] text-risk" : "bg-[#eef2ef] text-sage"}`}>
              {finding.severity} / {finding.confidence}
            </span>
          </div>
          <p className="mt-3 text-sm leading-6">{finding.description}</p>
          <p className="mt-2 text-sm leading-6 text-sage">{finding.why_it_matters}</p>
          <div className="mt-3 rounded-md border border-line bg-white p-3 text-sm">
            <span className="font-semibold">Recommended fix: </span>
            {finding.recommended_fix}
          </div>
          <div className="mt-3 space-y-2">
            {finding.supporting_sources.map((source, index) => (
              <div key={index} className="rounded-md border border-line bg-white p-3 text-xs leading-5 text-sage">
                <div>
                  {String(source.source_type)} | {String(source.source_id)} | {String(source.timestamp ?? source.page ?? "source")}
                </div>
                <div className="mt-1 text-ink">{String(source.quote ?? "")}</div>
              </div>
            ))}
          </div>
        </article>
      ))}
      {findings.length === 0 ? <div className="rounded-md border border-line bg-panel p-5 text-sm text-sage shadow-warroom">No findings in this category.</div> : null}
    </section>
  );
}

function JudgeViews({ judges }: { judges: Array<{ id: string; persona: string; output: Record<string, unknown>; confidence: string }> }) {
  return (
    <section className="grid grid-cols-3 gap-3">
      {judges.map((judge) => (
        <article key={judge.id} className="rounded-md border border-line bg-panel p-4 shadow-warroom">
          <div className="font-semibold">{judge.persona}</div>
          <p className="mt-2 text-sm leading-6">{String(judge.output.tentative_view ?? "")}</p>
          <div className="mt-3 text-xs uppercase tracking-wide text-sage">Top concerns</div>
          <ul className="mt-2 space-y-1 text-sm">
            {Array.isArray(judge.output.top_concerns)
              ? judge.output.top_concerns.map((concern, index) => <li key={index}>• {String(concern)}</li>)
              : null}
          </ul>
        </article>
      ))}
    </section>
  );
}

function Transcript({ turns }: { turns: Array<{ id: string; round_number: number; turn_number: number; agent_role: string; model_provider?: string | null; model_name?: string | null; output: Record<string, unknown> }> }) {
  return (
    <section className="rounded-md border border-line bg-panel p-5 shadow-warroom">
      <div className="space-y-3">
        {turns.map((turn) => (
          <article key={turn.id} className="rounded-md border border-line bg-white p-3 text-sm">
            <div className="font-semibold">
              Round {turn.round_number}, Turn {turn.turn_number}: {turn.agent_role}
            </div>
            <div className="mt-1 text-xs text-sage">
              {turn.model_provider}/{turn.model_name}
            </div>
            <p className="mt-2 leading-6">{String(turn.output.claim ?? turn.output.tentative_view ?? "")}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

