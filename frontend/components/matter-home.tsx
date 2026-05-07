"use client";

import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, BrainCircuit, FileText, Mail, Play } from "lucide-react";
import { api } from "@/lib/api";
import type { Matter, Simulation } from "@/lib/types";
import { Button } from "./ui/button";

export function MatterHome({ matter, onSimulationSelected }: { matter: Matter; onSimulationSelected: (simulation: Simulation) => void }) {
  const documents = useQuery({ queryKey: ["documents", matter.id], queryFn: () => api.documents(matter.id) });
  const emails = useQuery({ queryKey: ["emails", matter.id], queryFn: () => api.emails(matter.id) });
  const simulations = useQuery({ queryKey: ["simulations", matter.id], queryFn: () => api.simulations(matter.id) });

  const latest = simulations.data?.[0];
  return (
    <div className="space-y-5">
      <section className="grid grid-cols-4 gap-4">
        <StatusPanel icon={FileText} label="Document Library" value={`${documents.data?.length ?? 0} files`} status="Upload and classify legal materials" />
        <StatusPanel icon={Mail} label="Email Timeline" value={`${emails.data?.length ?? 0} events`} status="Notice, waiver, delay, and contradiction signals" />
        <StatusPanel icon={BrainCircuit} label="Self-Play" value={`${simulations.data?.length ?? 0} runs`} status="Multi-round adversarial simulation state" />
        <StatusPanel icon={AlertTriangle} label="Latest Risk" value={(latest?.summary?.finding_count as number | undefined)?.toString() ?? "0"} status="Structured vulnerabilities found" />
      </section>
      <section className="grid grid-cols-[1.2fr_0.8fr] gap-4">
        <div className="rounded-md border border-line bg-panel p-5 shadow-warroom">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="text-lg font-semibold">Matter Control Board</h2>
            {latest ? (
              <Button variant="secondary" onClick={() => onSimulationSelected(latest)}>
                <Play size={16} />
                Open Latest Arena
              </Button>
            ) : null}
          </div>
          <div className="grid grid-cols-2 gap-3 text-sm">
            <ChecklistItem done={(documents.data?.length ?? 0) > 0} label="Create local matter and upload record materials" />
            <ChecklistItem done={(emails.data?.length ?? 0) > 0} label="Parse email chronology and legal event tags" />
            <ChecklistItem done label="Configure visible model routing with mock provider default" />
            <ChecklistItem done={(simulations.data?.length ?? 0) > 0} label="Run multi-turn self-play with judge personas" />
            <ChecklistItem done={(latest?.findings?.length ?? 0) > 0} label="Generate structured source-linked findings" />
            <ChecklistItem done={Boolean(latest?.summary)} label="Export vulnerability memo from final run" />
          </div>
        </div>
        <div className="rounded-md border border-line bg-panel p-5 shadow-warroom">
          <h2 className="text-lg font-semibold">Latest Simulation</h2>
          {latest ? (
            <div className="mt-4 space-y-3 text-sm">
              <div className="flex justify-between border-b border-line pb-2">
                <span>Status</span>
                <span className="font-semibold">{latest.status}</span>
              </div>
              <div className="flex justify-between border-b border-line pb-2">
                <span>Rounds</span>
                <span className="font-semibold">{String(latest.summary?.rounds_completed ?? "-")}</span>
              </div>
              <div className="flex justify-between border-b border-line pb-2">
                <span>Findings</span>
                <span className="font-semibold">{String(latest.summary?.finding_count ?? "-")}</span>
              </div>
              <div className="rounded-md bg-[#f0eadc] p-3 text-sage">
                {Array.isArray(latest.summary?.top_vulnerabilities)
                  ? latest.summary.top_vulnerabilities.slice(0, 3).join(" | ")
                  : "No vulnerabilities yet."}
              </div>
            </div>
          ) : (
            <p className="mt-4 text-sm text-sage">No run yet. Configure a simulation to create a transcript, findings, and memo.</p>
          )}
        </div>
      </section>
    </div>
  );
}

function StatusPanel({
  icon: Icon,
  label,
  value,
  status
}: {
  icon: React.ElementType;
  label: string;
  value: string;
  status: string;
}) {
  return (
    <div className="rounded-md border border-line bg-panel p-4 shadow-warroom">
      <div className="mb-3 flex items-center justify-between">
        <Icon size={18} className="text-docket" />
        <span className="rounded-sm bg-[#eef2ef] px-2 py-1 text-xs text-sage">{value}</span>
      </div>
      <h3 className="font-semibold">{label}</h3>
      <p className="mt-1 text-xs leading-5 text-sage">{status}</p>
    </div>
  );
}

function ChecklistItem({ done, label }: { done: boolean; label: string }) {
  return (
    <div className="flex items-center gap-2 rounded-md border border-line bg-white px-3 py-2">
      <span className={`h-2.5 w-2.5 rounded-full ${done ? "bg-sage" : "bg-amber"}`} />
      <span>{label}</span>
    </div>
  );
}

