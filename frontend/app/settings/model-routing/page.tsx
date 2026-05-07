"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { ModelRouting } from "@/components/model-routing";
import { Button } from "@/components/ui/button";

const queryClient = new QueryClient();

export default function ModelRoutingPage() {
  return (
    <QueryClientProvider client={queryClient}>
      <main className="min-h-screen bg-paper px-6 py-5 text-ink">
        <div className="mb-5">
          <Link href="/">
            <Button variant="secondary">
              <ArrowLeft size={16} />
              Back to War Room
            </Button>
          </Link>
        </div>
        <ModelRouting />
      </main>
    </QueryClientProvider>
  );
}

