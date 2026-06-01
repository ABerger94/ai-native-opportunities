import Link from "next/link";
import { ArrowLeft, ExternalLink } from "lucide-react";
import { notFound } from "next/navigation";
import { getMatchReport } from "@/lib/api";
import { Badge, Score } from "@/components/ui";

type PageProps = {
  params: Promise<{ id: string }>;
};

export default async function MatchReportPage({ params }: PageProps) {
  const { id } = await params;
  const match = await getMatchReport(id).catch(() => null);

  if (!match) {
    notFound();
  }

  const opportunity = match.opportunity;
  const company = opportunity.company?.name ?? opportunity.source;
  const positiveSignals = match.explanation.positive_signals ?? [];
  const missing = [...match.missing_skills, ...match.missing_experience];
  const preparationTime = match.explanation.preparation_time ?? "Not estimated";
  const strengthsSummary = positiveSignals.length
    ? positiveSignals.slice(0, 4).join(", ")
    : "The match engine did not find strong direct evidence yet.";

  return (
    <main className="min-h-screen">
      <header className="border-b border-border bg-card">
        <div className="mx-auto max-w-7xl px-6 py-6">
          <Link className="inline-flex items-center gap-2 text-sm font-medium text-muted-foreground hover:text-foreground" href="/">
            <ArrowLeft className="h-4 w-4" />
            Back to dashboard
          </Link>
          <div className="mt-5 flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
            <div className="max-w-4xl">
              <p className="text-sm font-medium text-primary">Capability Report</p>
              <h1 className="mt-2 text-3xl font-semibold tracking-normal">{opportunity.title}</h1>
              <p className="mt-2 text-sm text-muted-foreground">
                {company}
                {opportunity.location ? ` - ${opportunity.location}` : ""}
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                <Badge>{formatFitBand(match.fit_band)}</Badge>
                <Badge>{opportunity.opportunity_type}</Badge>
                <Badge>{preparationTime}</Badge>
                {opportunity.remote ? <Badge>Remote or hybrid</Badge> : null}
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

      <section className="mx-auto grid max-w-7xl gap-6 px-6 py-6 lg:grid-cols-[1fr_380px]">
        <div className="grid gap-6">
          <ReportSection title="Role Fit Summary">
            <p className="text-sm leading-7 text-muted-foreground">
              Your current fit is <strong className="text-foreground">{match.overall_match_score}%</strong>. The strongest evidence is {strengthsSummary}. The main path to a stronger application is closing gaps in {missing.slice(0, 5).join(", ") || "role-specific proof"}.
            </p>
          </ReportSection>

          <ReportSection title="Capability Evidence">
            <CapabilityList items={positiveSignals} empty="No direct capability evidence was detected from the resume text." />
          </ReportSection>

          <ReportSection title="Gaps To Close">
            <CapabilityList items={missing} empty="No major gaps were detected." />
          </ReportSection>

          <ReportSection title="Preparation Plan">
            <div className="grid gap-4 md:grid-cols-3">
              <PlanStep title="Week 1" body="Translate your resume into role language. Add measurable examples for AI, automation, operations, product, and process improvement." />
              <PlanStep title="Weeks 2-3" body="Build or document one small AI workflow project that proves the missing skills from this role." />
              <PlanStep title="Before applying" body="Create a short portfolio case study and tailor the first third of your resume to this job's strongest signals." />
            </div>
          </ReportSection>

          <ReportSection title="Recommended Portfolio Proof">
            <CapabilityList
              items={[
                ...match.recommended_projects,
                ...match.recommended_portfolio_pieces,
                "One-page role-specific case study showing problem, workflow, AI tools used, measurable result, and handoff documentation."
              ]}
              empty="No portfolio recommendations were generated."
            />
          </ReportSection>

          <ReportSection title="Application Strategy">
            <CapabilityList
              items={[
                `Lead with ${positiveSignals[0] ?? "your strongest measurable business outcome"}.`,
                `Address ${missing[0] ?? "the largest capability gap"} with a concrete project or learning plan.`,
                "Use the cover letter to explain how you use AI as leverage, not just that you are interested in AI.",
                "Include links to a workflow demo, agent prototype, automation writeup, or product teardown when possible."
              ]}
              empty=""
            />
          </ReportSection>
        </div>

        <aside className="grid content-start gap-4">
          <section className="border border-border bg-card p-5">
            <h2 className="text-lg font-semibold">Score Breakdown</h2>
            <div className="mt-4 grid gap-4">
              <Score label="Overall Match" value={match.overall_match_score} />
              <Score label="Skill Match" value={match.skill_match_score} />
              <Score label="Experience Match" value={match.experience_match_score} />
              <Score label="AI Readiness" value={match.ai_readiness_score} />
              <Score label="Transition Probability" value={match.transition_probability} />
            </div>
          </section>

          <section className="border border-border bg-card p-5">
            <h2 className="text-lg font-semibold">Role Signals</h2>
            <div className="mt-4 flex flex-wrap gap-2">
              {opportunity.tools_mentioned.length ? (
                opportunity.tools_mentioned.map((tool) => <Badge key={tool}>{tool}</Badge>)
              ) : (
                <p className="text-sm text-muted-foreground">No explicit tools detected.</p>
              )}
            </div>
          </section>

          <section className="border border-border bg-card p-5">
            <h2 className="text-lg font-semibold">Resume Improvements</h2>
            <CapabilityList
              items={[
                "Move AI, automation, and workflow examples into the top summary.",
                "Quantify business impact: time saved, error reduction, revenue impact, cycle-time improvement.",
                "Add a projects section for agent workflows, AI automations, no-code systems, or rapid prototypes.",
                "Mirror the role's strongest tool language where you have real experience."
              ]}
              empty=""
            />
          </section>
        </aside>
      </section>
    </main>
  );
}

function ReportSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="border border-border bg-card p-6">
      <h2 className="text-lg font-semibold">{title}</h2>
      <div className="mt-4">{children}</div>
    </section>
  );
}

function CapabilityList({ items, empty }: { items: string[]; empty: string }) {
  const uniqueItems = Array.from(new Set(items.filter(Boolean)));
  if (!uniqueItems.length) {
    return empty ? <p className="text-sm text-muted-foreground">{empty}</p> : null;
  }
  return (
    <ul className="grid gap-2 text-sm leading-6 text-muted-foreground">
      {uniqueItems.slice(0, 10).map((item) => <li key={item}>- {item}</li>)}
    </ul>
  );
}

function PlanStep({ title, body }: { title: string; body: string }) {
  return (
    <div className="border border-border bg-background p-4">
      <h3 className="text-sm font-semibold">{title}</h3>
      <p className="mt-2 text-sm leading-6 text-muted-foreground">{body}</p>
    </div>
  );
}

function formatFitBand(value: string) {
  return value.replaceAll("_", " ");
}
