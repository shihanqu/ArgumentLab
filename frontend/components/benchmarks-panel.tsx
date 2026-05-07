"use client";

import { useMutation, useQuery } from "@tanstack/react-query";
import { Gauge, PlayCircle } from "lucide-react";
import { api } from "@/lib/api";
import { Button } from "./ui/button";

export function BenchmarksPanel() {
  const packets = useQuery({ queryKey: ["benchmark-packets"], queryFn: api.benchmarkPackets });
  const run = useMutation({ mutationFn: (packetId: string) => api.runBenchmark(packetId) });

  return (
    <div className="grid grid-cols-[1fr_420px] gap-4">
      <section className="rounded-md border border-line bg-panel p-5 shadow-warroom">
        <h2 className="text-lg font-semibold">Regression Benchmark Packets</h2>
        <div className="mt-4 grid gap-3">
          {(packets.data ?? []).map((packet) => (
            <article key={packet.id} className="rounded-md border border-line bg-white p-4">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="font-semibold">{packet.name}</div>
                  <p className="mt-1 text-sm leading-6 text-sage">{packet.description}</p>
                  <div className="mt-2 flex flex-wrap gap-1">
                    {packet.planted_issues.map((issue) => (
                      <span key={issue} className="rounded-sm bg-[#eef2ef] px-2 py-1 text-xs text-docket">
                        {issue}
                      </span>
                    ))}
                  </div>
                </div>
                <Button variant="secondary" onClick={() => run.mutate(packet.id)} disabled={run.isPending}>
                  <PlayCircle size={16} />
                  Run
                </Button>
              </div>
            </article>
          ))}
        </div>
      </section>
      <aside className="rounded-md border border-line bg-panel p-5 shadow-warroom">
        <h3 className="flex items-center gap-2 font-semibold">
          <Gauge size={17} />
          Last Benchmark Result
        </h3>
        <pre className="mt-4 max-h-[720px] overflow-auto whitespace-pre-wrap rounded-md border border-line bg-white p-3 text-xs">
          {run.data ? JSON.stringify(run.data, null, 2) : "No benchmark run yet."}
        </pre>
      </aside>
    </div>
  );
}

