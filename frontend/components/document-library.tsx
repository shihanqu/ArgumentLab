"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Upload, FileSearch } from "lucide-react";
import { useMemo, useState } from "react";
import { api } from "@/lib/api";
import { Button } from "./ui/button";
import { Label, Select } from "./ui/field";

const documentTypes = ["pleading", "motion", "opposition", "reply", "exhibit", "contract", "transcript", "email", "authority", "correspondence", "other"];

export function DocumentLibrary({ matterId }: { matterId: string }) {
  const qc = useQueryClient();
  const [files, setFiles] = useState<FileList | null>(null);
  const [manualType, setManualType] = useState("");
  const documents = useQuery({ queryKey: ["documents", matterId], queryFn: () => api.documents(matterId) });
  const upload = useMutation({
    mutationFn: () => {
      const form = new FormData();
      Array.from(files ?? []).forEach((file) => form.append("files", file));
      if (manualType) form.append("document_type", manualType);
      return api.uploadDocuments(matterId, form);
    },
    onSuccess: async () => {
      setFiles(null);
      await Promise.all([
        qc.invalidateQueries({ queryKey: ["documents", matterId] }),
        qc.invalidateQueries({ queryKey: ["emails", matterId] }),
        qc.invalidateQueries({ queryKey: ["matters"] })
      ]);
    }
  });
  const [selectedDocId, setSelectedDocId] = useState<string | null>(null);
  const selectedDoc = useMemo(() => documents.data?.find((doc) => doc.id === selectedDocId) ?? documents.data?.[0], [documents.data, selectedDocId]);

  return (
    <div className="grid grid-cols-[420px_1fr] gap-4">
      <section className="rounded-md border border-line bg-panel p-5 shadow-warroom">
        <h2 className="text-lg font-semibold">Upload / Document Library</h2>
        <div className="mt-4 rounded-md border border-dashed border-sage bg-white p-4">
          <Label>Drag/drop or select files</Label>
          <input
            type="file"
            multiple
            onChange={(event) => setFiles(event.target.files)}
            className="w-full rounded-md border border-line bg-panel p-3 text-sm"
          />
          <div className="mt-3">
            <Label>Manual type assignment</Label>
            <Select value={manualType} onChange={(event) => setManualType(event.target.value)}>
              <option value="">Auto-classify</option>
              {documentTypes.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </Select>
          </div>
          <Button className="mt-3 w-full" onClick={() => upload.mutate()} disabled={!files?.length || upload.isPending}>
            <Upload size={16} />
            Upload and Parse
          </Button>
        </div>
        <div className="mt-4 space-y-2">
          {(documents.data ?? []).map((doc) => (
            <button
              key={doc.id}
              onClick={() => setSelectedDocId(doc.id)}
              className={`w-full rounded-md border p-3 text-left text-sm ${selectedDoc?.id === doc.id ? "border-ink bg-[#f0eadc]" : "border-line bg-white"}`}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="truncate font-semibold">{doc.filename}</span>
                <span className="rounded-sm bg-[#eef2ef] px-2 py-1 text-xs text-sage">{doc.document_type}</span>
              </div>
              <div className="mt-1 text-xs text-sage">{doc.status} | {(doc.size_bytes / 1024).toFixed(1)} KB</div>
            </button>
          ))}
        </div>
      </section>
      <section className="min-w-0 rounded-md border border-line bg-panel p-5 shadow-warroom">
        <div className="mb-4 flex items-center justify-between">
          <h2 className="text-lg font-semibold">Parsed Text Preview</h2>
          <FileSearch size={18} className="text-docket" />
        </div>
        {selectedDoc ? (
          <div className="space-y-4">
            <DocTypeEditor matterId={matterId} documentId={selectedDoc.id} value={selectedDoc.document_type} />
            <div className="rounded-md border border-line bg-white p-3 text-xs leading-5 text-sage">{selectedDoc.classification_reason}</div>
            <pre className="max-h-[620px] overflow-auto whitespace-pre-wrap rounded-md border border-line bg-white p-4 text-sm leading-6">
              {selectedDoc.extracted_text || "No text extracted."}
            </pre>
          </div>
        ) : (
          <p className="text-sm text-sage">Upload a draft motion, opposition, pleading, exhibit, authority, transcript, contract, or email history to begin.</p>
        )}
      </section>
    </div>
  );
}

function DocTypeEditor({ matterId, documentId, value }: { matterId: string; documentId: string; value: string }) {
  const qc = useQueryClient();
  const mutation = useMutation({
    mutationFn: (documentType: string) => api.patchDocument(matterId, documentId, documentType),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["documents", matterId] })
  });
  return (
    <div className="max-w-xs">
      <Label>Document type</Label>
      <Select value={value} onChange={(event) => mutation.mutate(event.target.value)}>
        {documentTypes.map((type) => (
          <option key={type} value={type}>
            {type}
          </option>
        ))}
      </Select>
    </div>
  );
}

