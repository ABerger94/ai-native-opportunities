"use client";

import Link from "next/link";
import { useState } from "react";
import { ArrowRight, Import } from "lucide-react";
import { Button } from "@/components/ui";
import type { Opportunity } from "@/lib/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export function ManualOpportunityImporter() {
  const [source, setSource] = useState("LinkedIn");
  const [url, setUrl] = useState("");
  const [title, setTitle] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [location, setLocation] = useState("Remote");
  const [opportunityType, setOpportunityType] = useState("job");
  const [description, setDescription] = useState("");
  const [notes, setNotes] = useState("");
  const [status, setStatus] = useState("Paste any job, contract, or project you found manually and import it for AI-native scoring.");
  const [opportunity, setOpportunity] = useState<Opportunity | null>(null);
  const [busy, setBusy] = useState(false);

  async function importOpportunity() {
    setBusy(true);
    setOpportunity(null);
    setStatus("Importing opportunity...");
    try {
      const response = await fetch(`${API_BASE_URL}/manual-opportunities/import`, {
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          source,
          url,
          title,
          company_name: companyName || null,
          description,
          location: location || "Remote",
          remote: /remote|hybrid|anywhere|distributed/i.test(`${location} ${description}`),
          opportunity_type: opportunityType,
          notes: notes || null
        })
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      const result = (await response.json()) as Opportunity;
      setOpportunity(result);
      setStatus("Imported, scored, and added to your opportunity database.");
      setUrl("");
      setTitle("");
      setCompanyName("");
      setDescription("");
      setNotes("");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Import failed.");
    } finally {
      setBusy(false);
    }
  }

  const disabled = busy || !url.trim() || !title.trim() || !description.trim();

  return (
    <section className="mx-auto max-w-7xl px-6 pb-6">
      <div className="border border-border bg-card p-5">
        <div className="flex flex-col gap-2">
          <p className="text-sm font-medium text-primary">Paste Any Job</p>
          <h2 className="text-xl font-semibold">Import LinkedIn, Indeed, Reddit, Slack, email, or company-page opportunities</h2>
          <p className="max-w-3xl text-sm leading-6 text-muted-foreground">{status}</p>
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          <label className="grid gap-1 text-sm font-medium">
            Source
            <select className="h-10 border border-border bg-background px-3 text-sm" value={source} onChange={(event) => setSource(event.target.value)}>
              {["LinkedIn", "Indeed", "Reddit", "Slack", "Discord", "Email", "Company Page", "Other"].map((option) => (
                <option key={option}>{option}</option>
              ))}
            </select>
          </label>
          <label className="grid gap-1 text-sm font-medium">
            Type
            <select className="h-10 border border-border bg-background px-3 text-sm" value={opportunityType} onChange={(event) => setOpportunityType(event.target.value)}>
              {["job", "freelance", "contract", "consulting", "fractional", "founder", "cofounder"].map((option) => (
                <option key={option} value={option}>{option}</option>
              ))}
            </select>
          </label>
          <label className="grid gap-1 text-sm font-medium md:col-span-2">
            URL
            <input className="h-10 border border-border bg-background px-3 text-sm" value={url} onChange={(event) => setUrl(event.target.value)} />
          </label>
          <label className="grid gap-1 text-sm font-medium">
            Title
            <input className="h-10 border border-border bg-background px-3 text-sm" value={title} onChange={(event) => setTitle(event.target.value)} />
          </label>
          <label className="grid gap-1 text-sm font-medium">
            Company / Client
            <input className="h-10 border border-border bg-background px-3 text-sm" value={companyName} onChange={(event) => setCompanyName(event.target.value)} />
          </label>
          <label className="grid gap-1 text-sm font-medium md:col-span-2">
            Location
            <input className="h-10 border border-border bg-background px-3 text-sm" value={location} onChange={(event) => setLocation(event.target.value)} />
          </label>
          <label className="grid gap-1 text-sm font-medium md:col-span-2">
            Description
            <textarea className="min-h-40 border border-border bg-background p-3 text-sm" value={description} onChange={(event) => setDescription(event.target.value)} />
          </label>
          <label className="grid gap-1 text-sm font-medium md:col-span-2">
            Notes
            <textarea className="min-h-24 border border-border bg-background p-3 text-sm" value={notes} onChange={(event) => setNotes(event.target.value)} />
          </label>
        </div>
        <div className="mt-4 flex flex-wrap items-center gap-4">
          <Button disabled={disabled} onClick={() => void importOpportunity()}>
            <Import className="mr-2 h-4 w-4" />
            Import Opportunity
          </Button>
          {opportunity ? (
            <Link className="inline-flex items-center gap-2 text-sm font-medium text-primary hover:underline" href={`/opportunities/${opportunity.id}`}>
              Open imported opportunity <ArrowRight className="h-4 w-4" />
            </Link>
          ) : null}
        </div>
      </div>
    </section>
  );
}
