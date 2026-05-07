"use client";

import ReactFlow, { Background, Controls, Edge, Node } from "reactflow";
import "reactflow/dist/style.css";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export function IssueMap({ matterId }: { matterId: string }) {
  const documents = useQuery({ queryKey: ["documents", matterId], queryFn: () => api.documents(matterId) });
  const emails = useQuery({ queryKey: ["emails", matterId], queryFn: () => api.emails(matterId) });
  const nodes: Node[] = [
    node("issue", "Issue", 40, 80),
    node("argument", "User Argument", 240, 80),
    node("fact", "Supporting Facts", 480, 20),
    node("evidence", "Evidence", 720, 20),
    node("authority", "Authority", 720, 140),
    node("counter", "Counterargument", 480, 180),
    node("judge", "Judge Concern", 240, 220)
  ];
  const edges: Edge[] = [
    edge("issue", "argument"),
    edge("argument", "fact"),
    edge("fact", "evidence"),
    edge("argument", "authority"),
    edge("argument", "counter"),
    edge("counter", "judge")
  ];

  return (
    <div className="grid grid-cols-[1fr_340px] gap-4">
      <section className="h-[720px] rounded-md border border-line bg-panel p-3 shadow-warroom">
        <ReactFlow nodes={nodes} edges={edges} fitView>
          <Background color="#d7d0c1" gap={18} />
          <Controls />
        </ReactFlow>
      </section>
      <section className="rounded-md border border-line bg-panel p-5 shadow-warroom">
        <h2 className="text-lg font-semibold">Issue Map Inputs</h2>
        <div className="mt-4 space-y-3 text-sm">
          <MapBlock title="Claim" value="Configured side and procedural posture from simulation setup." />
          <MapBlock title="Fact" value={`${documents.data?.length ?? 0} uploaded document(s) supply source snippets.`} />
          <MapBlock title="Evidence" value="Source references are page/snippet based in v0.1." />
          <MapBlock title="Authority" value="Uploaded-only authority support; good-law status is not checked." />
          <MapBlock title="Email chronology" value={`${emails.data?.length ?? 0} email event(s) available for notice, waiver, modification, and contradiction checks.`} />
        </div>
      </section>
    </div>
  );
}

function node(id: string, label: string, x: number, y: number): Node {
  return {
    id,
    position: { x, y },
    data: { label },
    style: {
      border: "1px solid #d7d0c1",
      borderRadius: 6,
      padding: 12,
      background: "#fffdf7",
      color: "#18201f",
      fontSize: 13,
      width: 170
    }
  };
}

function edge(source: string, target: string): Edge {
  return { id: `${source}-${target}`, source, target, animated: true, style: { stroke: "#315f72" } };
}

function MapBlock({ title, value }: { title: string; value: string }) {
  return (
    <div className="rounded-md border border-line bg-white p-3">
      <div className="font-semibold">{title}</div>
      <div className="mt-1 text-sage">{value}</div>
    </div>
  );
}

