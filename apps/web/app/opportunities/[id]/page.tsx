import Link from "next/link";
import { ArrowLeft, Building2, CalendarDays, ExternalLink, MapPin } from "lucide-react";
import { notFound } from "next/navigation";
import { getOpportunity } from "@/lib/api";
import { formatDate, htmlToText } from "@/lib/format";
import { Badge, Score } from "@/components/ui";

type PageProps = {
  params: Promise<{ id: string }>;
};

export default async function OpportunityDetailPage({ params }: PageProps) {
  const { id } = await params;
  const opportunity = await getOpportunity(id).catch(() => null);

  if (!opportunity) {
    notFound();
  }

  const companyName = opportunity.company?.name ?? opportunity.source;
  const description = htmlToText(opportunity.description);
  const positiveSignals = opportunity.score_explanation.positive_signals ?? [];
  const negativeSignals = opportunity.score_explanation.negative_signals ?? [];
  const categories = opportunity.score_explanation.freelance_categories ?? [];

  return (
    <main className="min-h-screen">
      <header className="border-b border-border bg-card">
        <div className="mx-auto max-w-7xl px-6 py-6">
          <Link className="inline-flex items-center gap-2 text-sm font-medium text-muted-foreground hover:text-foreground" href="/">
            <ArrowLeft className="h-4 w-4" />
            Back to opportunities
          </Link>
          <div className="mt-5 flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
            <div className="max-w-4xl">
              <div className="flex flex-wrap gap-2">
                <Badge>{opportunity.opportunity_type}</Badge>
                <Badge>{opportunity.source}</Badge>
                {opportunity.remote ? <Badge>Remote</Badge> : null}
              </div>
              <h1 className="mt-4 text-3xl font-semibold tracking-normal">{opportunity.title}</h1>
              <div className="mt-3 flex flex-wrap gap-x-5 gap-y-2 text-sm text-muted-foreground">
                <span className="inline-flex items-center gap-2">
                  <Building2 className="h-4 w-4" />
                  {companyName}
                </span>
                <span className="inline-flex items-center gap-2">
                  <MapPin className="h-4 w-4" />
                  {opportunity.location ?? "Location not listed"}
                </span>
                <span className="inline-flex items-center gap-2">
                  <CalendarDays className="h-4 w-4" />
                  Discovered {formatDate(opportunity.discovered_at)}
                </span>
              </div>
            </div>
            <a
              className="inline-flex h-11 items-center justify-center gap-2 rounded-md bg-primary px-5 text-sm font-medium text-primary-foreground transition hover:opacity-90"
              href={opportunity.url}
              target="_blank"
              rel="noreferrer"
            >
              Apply on source site <ExternalLink className="h-4 w-4" />
            </a>
          </div>
        </div>
      </header>

      <section className="mx-auto grid max-w-7xl gap-6 px-6 py-6 lg:grid-cols-[1fr_360px]">
        <article className="border border-border bg-card p-6">
          <h2 className="text-lg font-semibold">Opportunity Details</h2>
          <div className="mt-4 whitespace-pre-line text-sm leading-7 text-foreground">
            {description || "No description was provided by the source."}
          </div>
        </article>

        <aside className="grid content-start gap-4">
          <section className="border border-border bg-card p-5">
            <h2 className="text-lg font-semibold">Scores</h2>
            <div className="mt-4 grid gap-4">
              <Score label="AI Native" value={opportunity.ai_native_score} />
              <Score label="Opportunity" value={opportunity.opportunity_score} />
              <Score label="Freelance AI" value={opportunity.freelance_ai_score} />
            </div>
          </section>

          <section className="border border-border bg-card p-5">
            <h2 className="text-lg font-semibold">AI Signals</h2>
            <div className="mt-4 flex flex-wrap gap-2">
              {opportunity.tools_mentioned.length ? (
                opportunity.tools_mentioned.map((tool) => <Badge key={tool}>{tool}</Badge>)
              ) : (
                <p className="text-sm text-muted-foreground">No AI tools were explicitly detected.</p>
              )}
            </div>
          </section>

          <section className="border border-border bg-card p-5">
            <h2 className="text-lg font-semibold">Why It Ranked</h2>
            <List items={positiveSignals} empty="No positive signals were captured." />
            {negativeSignals.length ? (
              <>
                <h3 className="mt-5 text-sm font-semibold">Watchouts</h3>
                <List items={negativeSignals} empty="" />
              </>
            ) : null}
          </section>

          <section className="border border-border bg-card p-5">
            <h2 className="text-lg font-semibold">Profile</h2>
            <dl className="mt-4 grid gap-3 text-sm">
              <Meta label="Company" value={companyName} />
              <Meta label="Posted" value={formatDate(opportunity.posted_at)} />
              <Meta label="External ID" value={opportunity.external_id} />
              <Meta label="Budget" value={formatMoneyRange(opportunity.budget_min, opportunity.budget_max)} />
              <Meta label="Hourly" value={formatMoneyRange(opportunity.hourly_min, opportunity.hourly_max)} />
            </dl>
          </section>

          {categories.length ? (
            <section className="border border-border bg-card p-5">
              <h2 className="text-lg font-semibold">Relevant Categories</h2>
              <div className="mt-4 flex flex-wrap gap-2">
                {categories.map((category) => <Badge key={category}>{category}</Badge>)}
              </div>
            </section>
          ) : null}
        </aside>
      </section>
    </main>
  );
}

function List({ items, empty }: { items: string[]; empty: string }) {
  if (!items.length) {
    return empty ? <p className="mt-3 text-sm text-muted-foreground">{empty}</p> : null;
  }
  return (
    <ul className="mt-3 grid gap-2 text-sm text-muted-foreground">
      {items.map((item) => <li key={item}>- {item}</li>)}
    </ul>
  );
}

function Meta({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-border pb-3 last:border-b-0 last:pb-0">
      <dt className="text-muted-foreground">{label}</dt>
      <dd className="text-right font-medium">{value}</dd>
    </div>
  );
}

function formatMoneyRange(min: number | null, max: number | null): string {
  if (min === null && max === null) {
    return "Not listed";
  }
  const formatter = new Intl.NumberFormat("en", { maximumFractionDigits: 0, style: "currency", currency: "USD" });
  if (min !== null && max !== null) {
    return `${formatter.format(min)} - ${formatter.format(max)}`;
  }
  return formatter.format(min ?? max ?? 0);
}
