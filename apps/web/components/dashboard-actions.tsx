"use client";

import { useState } from "react";
import { RefreshCw } from "lucide-react";
import { Button } from "@/components/ui";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export function DashboardActions() {
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

  return (
    <div className="flex flex-col gap-2">
      <div className="flex flex-wrap gap-3">
        <Button disabled={busy} className="bg-foreground" onClick={() => void runIngestion()}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Run Ingestion
        </Button>
      </div>
      {status ? <p className="max-w-md text-sm text-muted-foreground">{status}</p> : null}
    </div>
  );
}
