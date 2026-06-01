import Link from "next/link";
import { ArrowLeft, ArrowRight, ExternalLink, Filter, Search } from "lucide-react";
import { getOpportunities } from "@/lib/api";
import { Badge, Score } from "@/components/ui";

type PageProps = {
  searchParams: Promise<{
    q?: string;
    work_mode?: string;
    min_ai_score?: string;
  }>;
};

export default async function OpportunitiesPage({ searchParams }: PageProps) {
  const params = await searchParams;
  const q = params.q?.trim() ?? "";
  const workMode = params.work_mode === "hybrid" || params.work_mode === "remote" ? params.work_mode : "";
  const minAiScore = params.min_ai_score ? Number(params.min_ai_score) : 35;
  const opportunities = await getOpportunities({
    query: q,
    work_mode: workMode,
    min_ai_score: Number.isFinite(minAiScore) ? minAiScore : 35,
    limit: 100
  }).catch(() => []);

  const hasRemoteJobs = opportunities.some((opportunity) => opportunity.source.startsWith("remotejobs"));

  return (
    <main className="min-h-screen">
      <header className="border-b border-border bg-card">
        <div className="mx-auto max-w-7xl px-6 py-6">
          <Link className="inline-flex items-center gap-2 text-sm font-medium text-muted-foreground hover:text-foreground" href="/">
            <ArrowLeft className="h-4 w-4" />
            Back to dashboard
          </Link>
          <div className="mt-5 flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
            <div>
              <p className="text-sm font-medium text-primary">Remote and hybrid only</p>
              <h1 className="mt-1 text-3xl font-semibold tracking-normal">Opportunity Browse</h1>
            </div>
            <Badge>{opportunities.length} results</Badge>
          </div>
        </div>
      </header>

      <section className="mx-auto max-w-7xl px-6 py-6">
        <form className="grid gap-3 border border-border bg-card p-4 md:grid-cols-[1fr_180px_160px_auto]" action="/opportunities">
          <label className="grid gap-2 text-sm font-medium">
            Search
            <span className="relative">
              <Search className="pointer-events-none absolute left-3 top-2.5 h-4 w-4 text-muted-foreground" />
              <input
                className="h-10 w-full border border-border bg-background pl-9 pr-3 text-sm outline-none focus:border-primary"
                name="q"
                defaultValue={q}
                placeholder="agent, n8n, workflow, prompt..."
              />
            </span>
          </label>
          <label className="grid gap-2 text-sm font-medium">
            Work mode
            <select className="h-10 border border-border bg-background px-3 text-sm outline-none focus:border-primary" name="work_mode" defaultValue={workMode}>
              <option value="">Remote + hybrid</option>
              <option value="remote">Remote only</option>
              <option value="hybrid">Hybrid only</option>
            </select>
          </label>
          <label className="grid gap-2 text-sm font-medium">
            Min AI score
            <input
              className="h-10 border border-border bg-background px-3 text-sm outline-none focus:border-primary"
              name="min_ai_score"
              type="number"
              min="0"
              max="100"
              defaultValue={String(Number.isFinite(minAiScore) ? minAiScore : 35)}
            />
          </label>
          <button className="inline-flex h-10 items-center justify-center gap-2 self-end rounded-md bg-primary px-4 text-sm font-medium text-primary-foreground">
            <Filter className="h-4 w-4" />
            Apply
          </button>
        </form>

        {hasRemoteJobs ? (
          <p className="mt-3 text-xs text-muted-foreground">
            Some results are powered by{" "}
            <a className="font-medium text-primary hover:underline" href="https://remotejobs.org" target="_blank" rel="noreferrer">
              RemoteJobs.org
            </a>
            .
          </p>
        ) : null}
      </section>

      <section className="mx-auto grid max-w-7xl gap-3 px-6 pb-10">
        {opportunities.map((opportunity) => (
          <article key={opportunity.id} className="border border-border bg-card p-5">
            <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
              <div className="min-w-0">
                <div className="flex flex-wrap gap-2">
                  <Badge>{formatWorkMode(opportunity.work_mode, opportunity.work_mode_confidence)}</Badge>
                  <Badge>{opportunity.opportunity_type}</Badge>
                  <Badge>{opportunity.source}</Badge>
                </div>
                <Link className="mt-3 block text-lg font-semibold hover:underline" href={`/opportunities/${opportunity.id}`}>
                  {opportunity.title}
                </Link>
                <p className="mt-1 text-sm text-muted-foreground">
                  {opportunity.company?.name ?? opportunity.source} {opportunity.location ? `- ${opportunity.location}` : ""}
                </p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {opportunity.tools_mentioned.slice(0, 6).map((tool) => (
                    <Badge key={tool}>{tool}</Badge>
                  ))}
                </div>
                <div className="mt-4 flex flex-wrap gap-4 text-sm font-medium">
                  <Link className="inline-flex items-center gap-2 text-primary hover:underline" href={`/opportunities/${opportunity.id}`}>
                    Full profile <ArrowRight className="h-4 w-4" />
                  </Link>
                  <a className="inline-flex items-center gap-2 text-muted-foreground hover:text-foreground" href={opportunity.url} target="_blank" rel="noreferrer">
                    Apply link <ExternalLink className="h-4 w-4" />
                  </a>
                </div>
              </div>
              <div className="grid w-full gap-3 lg:w-64">
                <Score label="AI Native" value={opportunity.ai_native_score} />
                <Score label="Opportunity" value={opportunity.opportunity_score} />
                <Score label="Freelance AI" value={opportunity.freelance_ai_score} />
              </div>
            </div>
          </article>
        ))}
        {!opportunities.length ? (
          <div className="border border-border bg-card p-8">
            <h2 className="text-lg font-semibold">No matching opportunities</h2>
            <p className="mt-2 text-sm text-muted-foreground">Try a lower AI score or a broader keyword.</p>
          </div>
        ) : null}
      </section>
    </main>
  );
}

function formatWorkMode(workMode: string, confidence: number) {
  const normalized = workMode || "remote";
  const label = normalized[0].toUpperCase() + normalized.slice(1);
  return `${label} ${confidence}%`;
}
