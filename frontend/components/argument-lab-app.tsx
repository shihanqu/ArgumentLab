"use client";

import { QueryClient, QueryClientProvider, useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { Archive, BrainCircuit, FileText, Gavel, GitBranch, Home, Mail, Map, Play, Settings, ShieldAlert } from "lucide-react";
import { api } from "@/lib/api";
import type { Matter, Simulation } from "@/lib/types";
import { Button } from "./ui/button";
import { Input, Label } from "./ui/field";
import { MatterHome } from "./matter-home";
import { DocumentLibrary } from "./document-library";
import { EmailTimeline } from "./email-timeline";
import { IssueMap } from "./issue-map";
import { ModelRouting } from "./model-routing";
import { SimulationSetup } from "./simulation-setup";
import { SelfPlayArena } from "./self-play-arena";
import { FindingsDashboard } from "./findings-dashboard";
import { BenchmarksPanel } from "./benchmarks-panel";
import { cn } from "@/lib/utils";

const queryClient = new QueryClient();

type Screen = "home" | "documents" | "email" | "issues" | "routing" | "setup" | "arena" | "findings" | "benchmarks";

const navItems: Array<{ id: Screen; label: string; icon: React.ElementType }> = [
  { id: "home", label: "Matter Home", icon: Home },
  { id: "documents", label: "Documents", icon: FileText },
  { id: "email", label: "Email Timeline", icon: Mail },
  { id: "issues", label: "Issue Map", icon: Map },
  { id: "routing", label: "Model Routing", icon: Settings },
  { id: "setup", label: "Simulation Setup", icon: Play },
  { id: "arena", label: "Self-Play Arena", icon: BrainCircuit },
  { id: "findings", label: "Findings", icon: ShieldAlert },
  { id: "benchmarks", label: "Benchmarks", icon: Archive }
];

export function ArgumentLabApp() {
  return (
    <QueryClientProvider client={queryClient}>
      <WarRoom />
    </QueryClientProvider>
  );
}

function WarRoom() {
  const query = useQuery({ queryKey: ["matters"], queryFn: api.matters });
  const [selectedMatterId, setSelectedMatterId] = useState<string | null>(null);
  const [selectedSimulationId, setSelectedSimulationId] = useState<string | null>(null);
  const [screen, setScreen] = useState<Screen>("home");
  const matters = query.data ?? [];
  const selectedMatter = useMemo(
    () => matters.find((matter) => matter.id === selectedMatterId) ?? matters[0] ?? null,
    [matters, selectedMatterId]
  );

  return (
    <div className="min-h-screen text-ink">
      <div className="grid min-h-screen grid-cols-[280px_1fr]">
        <aside className="border-r border-line bg-[#eee8da] px-4 py-5">
          <div className="mb-6 flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-md bg-ink text-paper">
              <Gavel size={20} />
            </div>
            <div>
              <div className="text-lg font-semibold">Argument Lab</div>
              <div className="text-xs uppercase tracking-wide text-sage">Local War Room</div>
            </div>
          </div>
          <MatterPicker matters={matters} selectedMatter={selectedMatter} onSelect={setSelectedMatterId} />
          <nav className="mt-6 space-y-1">
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <button
                  key={item.id}
                  onClick={() => setScreen(item.id)}
                  className={cn(
                    "flex h-10 w-full items-center gap-3 rounded-md px-3 text-left text-sm transition",
                    screen === item.id ? "bg-ink text-paper" : "text-ink hover:bg-panel"
                  )}
                >
                  <Icon size={17} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
          <div className="mt-6 rounded-md border border-line bg-panel p-3 text-xs leading-5 text-sage">
            <div>AUTH_MODE=local</div>
            <div>STORAGE_MODE=local</div>
            <div>MODEL_GATEWAY=litellm</div>
          </div>
        </aside>
        <main className="min-w-0 px-6 py-5">
          <header className="mb-5 flex items-center justify-between border-b border-line pb-4">
            <div>
              <h1 className="text-2xl font-semibold">{selectedMatter?.name ?? "Create a Local Matter"}</h1>
              <p className="mt-1 max-w-3xl text-sm text-sage">
                Multi-turn adversarial self-play over uploaded legal materials, email chronology, model routes, and judge personas.
              </p>
            </div>
            {selectedMatter ? (
              <div className="grid grid-cols-3 gap-2 text-center text-xs">
                <Metric label="Docs" value={selectedMatter.document_count} />
                <Metric label="Emails" value={selectedMatter.email_count} />
                <Metric label="Runs" value={selectedMatter.simulation_count} />
              </div>
            ) : null}
          </header>
          {!selectedMatter ? (
            <CreateMatterPanel onCreated={(matter) => setSelectedMatterId(matter.id)} />
          ) : (
            <ScreenBody
              screen={screen}
              matter={selectedMatter}
              selectedSimulationId={selectedSimulationId}
              onSimulationSelected={(simulation) => {
                setSelectedSimulationId(simulation.id);
                setScreen("arena");
              }}
            />
          )}
        </main>
      </div>
    </div>
  );
}

function ScreenBody({
  screen,
  matter,
  selectedSimulationId,
  onSimulationSelected
}: {
  screen: Screen;
  matter: Matter;
  selectedSimulationId: string | null;
  onSimulationSelected: (simulation: Simulation) => void;
}) {
  if (screen === "documents") return <DocumentLibrary matterId={matter.id} />;
  if (screen === "email") return <EmailTimeline matterId={matter.id} />;
  if (screen === "issues") return <IssueMap matterId={matter.id} />;
  if (screen === "routing") return <ModelRouting />;
  if (screen === "setup") return <SimulationSetup matterId={matter.id} onSimulationCreated={onSimulationSelected} />;
  if (screen === "arena") return <SelfPlayArena matterId={matter.id} selectedSimulationId={selectedSimulationId} />;
  if (screen === "findings") return <FindingsDashboard matterId={matter.id} selectedSimulationId={selectedSimulationId} />;
  if (screen === "benchmarks") return <BenchmarksPanel />;
  return <MatterHome matter={matter} onSimulationSelected={onSimulationSelected} />;
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="min-w-20 rounded-md border border-line bg-panel px-3 py-2">
      <div className="text-lg font-semibold">{value}</div>
      <div className="uppercase tracking-wide text-sage">{label}</div>
    </div>
  );
}

function MatterPicker({
  matters,
  selectedMatter,
  onSelect
}: {
  matters: Matter[];
  selectedMatter: Matter | null;
  onSelect: (matterId: string) => void;
}) {
  return (
    <div>
      <Label>Local Matter</Label>
      <select
        value={selectedMatter?.id ?? ""}
        onChange={(event) => onSelect(event.target.value)}
        className="h-10 w-full rounded-md border border-line bg-panel px-3 text-sm"
      >
        {matters.length === 0 ? <option value="">No matters yet</option> : null}
        {matters.map((matter) => (
          <option key={matter.id} value={matter.id}>
            {matter.name}
          </option>
        ))}
      </select>
    </div>
  );
}

function CreateMatterPanel({ onCreated }: { onCreated: (matter: Matter) => void }) {
  const qc = useQueryClient();
  const [name, setName] = useState("New Litigation Stress Test");
  const [description, setDescription] = useState("");
  const mutation = useMutation({
    mutationFn: () => api.createMatter({ name, description }),
    onSuccess: async (matter) => {
      await qc.invalidateQueries({ queryKey: ["matters"] });
      onCreated(matter);
    }
  });
  return (
    <section className="max-w-2xl rounded-md border border-line bg-panel p-5 shadow-warroom">
      <h2 className="text-lg font-semibold">Create local matter</h2>
      <div className="mt-4 space-y-3">
        <div>
          <Label>Matter name</Label>
          <Input value={name} onChange={(event) => setName(event.target.value)} />
        </div>
        <div>
          <Label>Description</Label>
          <Input value={description} onChange={(event) => setDescription(event.target.value)} />
        </div>
        <Button onClick={() => mutation.mutate()} disabled={!name || mutation.isPending}>
          Create Matter
        </Button>
      </div>
    </section>
  );
}

