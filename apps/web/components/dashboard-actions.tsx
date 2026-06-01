"use client";

import { useRef, useState } from "react";
import { RefreshCw, Upload } from "lucide-react";
import { Button } from "@/components/ui";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export function DashboardActions() {
  const fileRef = useRef<HTMLInputElement>(null);
  const [status, setStatus] = useState<string>("");
  const [busy, setBusy] = useState(false);

  async function runIngestion() {
    setBusy(true);
    setStatus("Running ingestion from configured real sources...");
    try {
      const response = await fetch(`${API_BASE_URL}/ingestion/run`, { method: "POST" });
      if (!response.ok) throw new Error(await response.text());
      const result = (await response.json()) as { imported_count: number; source_count: number; errors: string[] };
      setStatus(`Imported ${result.imported_count} records from ${result.source_count} configured sources.`);
      window.location.reload();
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Ingestion failed.");
    } finally {
      setBusy(false);
    }
  }

  async function uploadResume(file: File | undefined) {
    if (!file) return;
    setBusy(true);
    setStatus("Uploading and parsing resume...");
    const form = new FormData();
    form.append("file", file);
    try {
      const response = await fetch(`${API_BASE_URL}/resumes?local_user_id=local-user`, {
        method: "POST",
        body: form
      });
      if (!response.ok) throw new Error(await response.text());
      const resume = (await response.json()) as { id: string };
      await fetch(`${API_BASE_URL}/resumes/${resume.id}/match`, { method: "POST" });
      setStatus("Resume parsed and matched against imported opportunities.");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Resume upload failed.");
    } finally {
      setBusy(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap gap-3">
        <input
          ref={fileRef}
          className="hidden"
          type="file"
          accept=".pdf,.docx,.txt"
          onChange={(event) => void uploadResume(event.target.files?.[0])}
        />
        <Button disabled={busy} onClick={() => fileRef.current?.click()}>
          <Upload className="mr-2 h-4 w-4" />
          Upload Resume
        </Button>
        <Button disabled={busy} className="bg-foreground" onClick={() => void runIngestion()}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Run Ingestion
        </Button>
      </div>
      {status ? <p className="max-w-md text-sm text-muted-foreground">{status}</p> : null}
    </div>
  );
}
