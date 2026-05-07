"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { MailPlus, Paperclip } from "lucide-react";
import { useState } from "react";
import { api } from "@/lib/api";
import { Button } from "./ui/button";
import { Input, Label, Textarea } from "./ui/field";

export function EmailTimeline({ matterId }: { matterId: string }) {
  const qc = useQueryClient();
  const emails = useQuery({ queryKey: ["emails", matterId], queryFn: () => api.emails(matterId) });
  const [subject, setSubject] = useState("");
  const [text, setText] = useState("");
  const mutation = useMutation({
    mutationFn: () => api.ingestCopiedThread(matterId, { subject, text }),
    onSuccess: async () => {
      setText("");
      await Promise.all([qc.invalidateQueries({ queryKey: ["emails", matterId] }), qc.invalidateQueries({ queryKey: ["matters"] })]);
    }
  });

  return (
    <div className="grid grid-cols-[380px_1fr] gap-4">
      <section className="rounded-md border border-line bg-panel p-5 shadow-warroom">
        <h2 className="text-lg font-semibold">Copied Email Thread</h2>
        <div className="mt-4 space-y-3">
          <div>
            <Label>Subject</Label>
            <Input value={subject} onChange={(event) => setSubject(event.target.value)} placeholder="Optional thread subject" />
          </div>
          <div>
            <Label>Thread text</Label>
            <Textarea value={text} onChange={(event) => setText(event.target.value)} placeholder="Paste email conversation history..." />
          </div>
          <Button onClick={() => mutation.mutate()} disabled={!text.trim() || mutation.isPending} className="w-full">
            <MailPlus size={16} />
            Parse Chronology
          </Button>
        </div>
      </section>
      <section className="rounded-md border border-line bg-panel p-5 shadow-warroom">
        <h2 className="text-lg font-semibold">Email Timeline</h2>
        <div className="mt-4 space-y-3">
          {(emails.data ?? []).map((email) => (
            <article key={email.id} className="rounded-md border border-line bg-white p-4">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <div className="text-sm font-semibold">
                    {formatDate(email.normalized_timestamp ?? email.original_timestamp)} → {email.sender ?? "Unknown sender"}
                  </div>
                  <div className="mt-1 text-xs text-sage">
                    To: {email.recipients.join(", ") || "unknown"} | {email.subject || "No subject"}
                  </div>
                </div>
                <div className="flex flex-wrap justify-end gap-1">
                  {email.legal_event_tags.map((tag) => (
                    <span key={tag} className="rounded-sm bg-[#eef2ef] px-2 py-1 text-xs text-docket">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
              <p className="mt-3 text-sm leading-6">{(email.normalized_body || email.raw_body || "").slice(0, 420)}</p>
              <div className="mt-3 flex flex-wrap items-center gap-3 text-xs text-sage">
                {email.detected_timezone ? <span>Timezone: {email.detected_timezone}</span> : null}
                {email.duplicate_quote_warning ? <span>Quoted history removed from normalized view</span> : null}
                {email.attachments.length ? (
                  <span className="inline-flex items-center gap-1">
                    <Paperclip size={13} />
                    {email.attachments.length} attachment(s)
                  </span>
                ) : null}
              </div>
            </article>
          ))}
          {emails.data?.length === 0 ? <p className="text-sm text-sage">No email events parsed yet. Upload `.eml`, `.mbox`, `.txt`, `.pdf` email exports, or paste a copied thread.</p> : null}
        </div>
      </section>
    </div>
  );
}

function formatDate(value?: string | null) {
  if (!value) return "Unknown date";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString();
}

