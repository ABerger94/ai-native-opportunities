"use client";

import Link from "next/link";
import { useState } from "react";
import { ArrowRight, Import } from "lucide-react";
import { Button } from "@/components/ui";
import type { Opportunity } from "@/lib/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export function RedditImporter() {
  const [url, setUrl] = useState("");
  const [title, setTitle] = useState("");
  const [subreddit, setSubreddit] = useState("");
  const [body, setBody] = useState("");
  const [status, setStatus] = useState("Paste a Reddit post from a public opportunity thread and import it for scoring.");
  const [opportunity, setOpportunity] = useState<Opportunity | null>(null);
  const [busy, setBusy] = useState(false);

  async function importPost() {
    setBusy(true);
    setStatus("Importing Reddit opportunity...");
    setOpportunity(null);
    try {
      const response = await fetch(`${API_BASE_URL}/reddit/import`, {
        method: "POST",
        headers: {
          Accept: "application/json",
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          url,
          title,
          body,
          subreddit: subreddit || null
        })
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      const result = (await response.json()) as Opportunity;
      setOpportunity(result);
      setStatus("Imported and scored as a real opportunity.");
      setUrl("");
      setTitle("");
      setSubreddit("");
      setBody("");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Reddit import failed.");
    } finally {
      setBusy(false);
    }
  }

  const disabled = busy || !url.trim() || !title.trim() || !body.trim();

  return (
    <section className="mx-auto max-w-7xl px-6 pb-6">
      <div className="border border-border bg-card p-5">
        <div className="flex flex-col gap-2">
          <p className="text-sm font-medium text-primary">Reddit Opportunity Import</p>
          <h2 className="text-xl font-semibold">Turn public Reddit posts into AI builder opportunities</h2>
          <p className="max-w-3xl text-sm leading-6 text-muted-foreground">{status}</p>
        </div>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          <label className="grid gap-1 text-sm font-medium">
            Reddit URL
            <input
              className="h-10 border border-border bg-background px-3 text-sm"
              placeholder="https://www.reddit.com/r/forhire/..."
              value={url}
              onChange={(event) => setUrl(event.target.value)}
            />
          </label>
          <label className="grid gap-1 text-sm font-medium">
            Subreddit
            <input
              className="h-10 border border-border bg-background px-3 text-sm"
              placeholder="forhire"
              value={subreddit}
              onChange={(event) => setSubreddit(event.target.value)}
            />
          </label>
          <label className="grid gap-1 text-sm font-medium md:col-span-2">
            Post title
            <input
              className="h-10 border border-border bg-background px-3 text-sm"
              placeholder="Need AI automation builder for n8n workflow"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
            />
          </label>
          <label className="grid gap-1 text-sm font-medium md:col-span-2">
            Post text
            <textarea
              className="min-h-32 border border-border bg-background p-3 text-sm"
              placeholder="Paste the public post body here. Include budget, timeline, tools, deliverables, and contact/application instructions if shown."
              value={body}
              onChange={(event) => setBody(event.target.value)}
            />
          </label>
        </div>
        <div className="mt-4 flex flex-wrap items-center gap-4">
          <Button disabled={disabled} onClick={() => void importPost()}>
            <Import className="mr-2 h-4 w-4" />
            Import Reddit Opportunity
          </Button>
          {opportunity ? (
            <Link
              className="inline-flex items-center gap-2 text-sm font-medium text-primary hover:underline"
              href={`/opportunities/${opportunity.id}`}
            >
              Open imported opportunity <ArrowRight className="h-4 w-4" />
            </Link>
          ) : null}
        </div>
      </div>
    </section>
  );
}
