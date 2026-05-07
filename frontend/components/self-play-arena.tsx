"use client";

import { useQuery } from "@tanstack/react-query";
import { BrainCircuit, GitBranch } from "lucide-react";
import { useMemo } from "react";
import { api } from "@/lib/api";
import type { SimulationTurn } from "@/lib/types";

export function SelfPlayArena({ matterId, selectedSimulationId }: { matterId: string; selectedSimulationId: string | null }) {
  const runs = useQuery({ queryKey: ["simulations", matterId], queryFn: () => api.simulations(matterId) });
  const chosenId = selectedSimulationId ?? runs.data?.[0]?.id;
  const detail = useQuery({ queryKey: ["simulation", chosenId], queryFn: () => api.simulation(chosenId as string), enabled: Boolean(chosenId) });
  const turnsByRound = useMemo(() => {
    const grouped = new Map<number, SimulationTurn[]>();
    for (const turn of detail.data?.turns ?? []) {
      grouped.set(turn.round_number, [...(grouped.get(turn.round_number) ?? []), turn]);
    }
    return Array.from(grouped.entries()).sort(([a], [b]) => a - b);
  }, [detail.data?.turns]);

  if (!chosenId) {
    return <div className="rounded-md border border-line bg-panel p-5 text-sm text-sage shadow-warroom">No simulation yet. Run one from Simulation Setup.</div>;
  }

  return (
    <div className="grid grid-cols-[1fr_320px] gap-4">
      <section className="rounded-md border border-line bg-panel p-5 shadow-warroom">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Self-Play Arena</h2>
          <div className="flex items-center gap-2 rounded-sm bg-[#eef2ef] px-2 py-1 text-xs text-sage">
            <BrainCircuit size={14} />
            {detail.data?.status ?? "loading"}
          </div>
        </div>
        <div className="space-y-4">
          {turnsByRound.map(([round, turns]) => (
            <div key={round} className="rounded-md border border-line bg-white">
              <div className="border-b border-line bg-[#f0eadc] px-4 py-3 text-sm font-semibold">Round {round}</div>
              <div className="divide-y divide-line">
                {turns.map((turn) => (
                  <article key={turn.id} className="p-4">
                    <div className="flex items-start justify-between gap-3">
                      <div>
                        <div className="font-semibold">{turn.agent_role}</div>
                        <div className="mt-1 text-xs text-sage">
                          Turn {turn.turn_number} | {turn.model_provider}/{turn.model_name} | confidence {turn.confidence}
                        </div>
                      </div>
                      <span className="rounded-sm bg-[#eef2ef] px-2 py-1 text-xs text-docket">{turn.agent_id}</span>
                    </div>
                    <p className="mt-3 text-sm leading-6">{String(turn.output.claim ?? turn.output.tentative_view ?? "")}</p>
                    {turn.new_findings.length ? (
                      <div className="mt-3 rounded-md border border-risk/30 bg-[#f7e5df] p-3 text-xs text-risk">
                        {turn.new_findings.map((finding, index) => (
                          <div key={index}>{String(finding.title)} | {String(finding.category)}</div>
                        ))}
                      </div>
                    ) : null}
                  </article>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>
      <aside className="rounded-md border border-line bg-panel p-5 shadow-warroom">
        <h3 className="flex items-center gap-2 font-semibold">
          <GitBranch size={16} />
          Run State
        </h3>
        <pre className="mt-4 max-h-[680px] overflow-auto whitespace-pre-wrap rounded-md border border-line bg-white p-3 text-xs">
          {JSON.stringify(detail.data?.summary ?? {}, null, 2)}
        </pre>
      </aside>
    </div>
  );
}
