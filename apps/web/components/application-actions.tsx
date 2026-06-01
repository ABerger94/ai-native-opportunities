"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Clipboard, ExternalLink, FileCheck } from "lucide-react";
import { Button } from "@/components/ui";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export function CreateApplicationButton({ matchId }: { matchId: string }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);

  async function createPacket() {
    setBusy(true);
    try {
      const response = await fetch(`${API_BASE_URL}/applications/from-match/${matchId}`, {
        method: "POST",
        headers: { Accept: "application/json" }
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      const application = (await response.json()) as { id: string };
      router.push(`/applications/${application.id}`);
    } finally {
      setBusy(false);
    }
  }

  return (
    <Button disabled={busy} onClick={() => void createPacket()}>
      <FileCheck className="mr-2 h-4 w-4" />
      Build application packet
    </Button>
  );
}

export function ApplicationStatusControls({ applicationId, applyUrl }: { applicationId: string; applyUrl: string }) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);

  async function update(status: string) {
    setBusy(true);
    try {
      await fetch(`${API_BASE_URL}/applications/${applicationId}`, {
        method: "PATCH",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ status })
      });
      router.refresh();
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex flex-wrap gap-3">
      <Button disabled={busy} onClick={() => void update("needs_review")}>
        Needs Review
      </Button>
      <Button disabled={busy} className="bg-foreground" onClick={() => void update("applied")}>
        Mark Applied
      </Button>
      <a
        className="inline-flex h-10 items-center justify-center gap-2 rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground transition hover:opacity-90"
        href={applyUrl}
        target="_blank"
        rel="noreferrer"
      >
        Open Apply Link <ExternalLink className="h-4 w-4" />
      </a>
    </div>
  );
}

export function CopyButton({ value, label = "Copy" }: { value: string; label?: string }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    await navigator.clipboard.writeText(value);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1500);
  }

  return (
    <button
      className="inline-flex items-center gap-2 text-sm font-medium text-primary hover:underline"
      onClick={() => void copy()}
      type="button"
    >
      <Clipboard className="h-4 w-4" />
      {copied ? "Copied" : label}
    </button>
  );
}
