import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { notFound } from "next/navigation";
import { getApplication } from "@/lib/api";
import { ApplicationStatusControls, CopyButton } from "@/components/application-actions";
import { Badge, Score } from "@/components/ui";

type PageProps = {
  params: Promise<{ id: string }>;
};

export default async function ApplicationWorkflowPage({ params }: PageProps) {
  const { id } = await params;
  const application = await getApplication(id).catch(() => null);

  if (!application) {
    notFound();
  }

  const match = application.match;
  const opportunity = match.opportunity;
  const packet = application.packet;
  const company = opportunity.company?.name ?? opportunity.source;

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
              <p className="text-sm font-medium text-primary">Application Workflow</p>
              <h1 className="mt-2 text-3xl font-semibold tracking-normal">{opportunity.title}</h1>
              <p className="mt-2 text-sm text-muted-foreground">
                {company}
                {opportunity.location ? ` - ${opportunity.location}` : ""}
              </p>
              <div className="mt-4 flex flex-wrap gap-2">
                <Badge>{application.status.replaceAll("_", " ")}</Badge>
                <Badge>{packet.fit_band.replaceAll("_", " ")}</Badge>
                <Badge>{opportunity.opportunity_type}</Badge>
              </div>
            </div>
            <ApplicationStatusControls applicationId={application.id} applyUrl={opportunity.url} />
          </div>
        </div>
      </header>

      <section className="mx-auto grid max-w-7xl gap-6 px-6 py-6 lg:grid-cols-[1fr_360px]">
        <div className="grid gap-6">
          <PacketSection title="Application Summary" copy={packet.summary}>
            <p className="text-sm leading-7 text-muted-foreground">{packet.summary}</p>
          </PacketSection>

          <PacketSection title="Role Pitch" copy={packet.pitch}>
            <p className="text-sm leading-7 text-muted-foreground">{packet.pitch}</p>
          </PacketSection>

          <PacketSection title="Cover Letter Draft" copy={packet.cover_letter}>
            <div className="whitespace-pre-line text-sm leading-7 text-muted-foreground">{packet.cover_letter}</div>
          </PacketSection>

          <PacketSection title="Short Application Answers">
            <div className="grid gap-4">
              {packet.short_answers.map((item) => (
                <div key={item.question} className="border border-border bg-background p-4">
                  <div className="flex items-start justify-between gap-4">
                    <h3 className="text-sm font-semibold">{item.question}</h3>
                    <CopyButton value={item.answer} />
                  </div>
                  <p className="mt-2 text-sm leading-6 text-muted-foreground">{item.answer}</p>
                </div>
              ))}
            </div>
          </PacketSection>

          <PacketSection title="Resume Focus">
            <List items={packet.resume_focus} />
          </PacketSection>

          <PacketSection title="Human Review Checklist">
            <List items={packet.review_checklist} />
          </PacketSection>
        </div>

        <aside className="grid content-start gap-4">
          <section className="border border-border bg-card p-5">
            <h2 className="text-lg font-semibold">Fit Scores</h2>
            <div className="mt-4 grid gap-4">
              <Score label="Overall Match" value={match.overall_match_score} />
              <Score label="Skill Match" value={match.skill_match_score} />
              <Score label="Experience" value={match.experience_match_score} />
              <Score label="AI Readiness" value={match.ai_readiness_score} />
              <Score label="Transition" value={match.transition_probability} />
            </div>
          </section>

          <section className="border border-border bg-card p-5">
            <h2 className="text-lg font-semibold">Gaps To Address</h2>
            <List items={packet.gaps_to_address} empty="No major gaps detected." />
          </section>

          <section className="border border-border bg-card p-5">
            <h2 className="text-lg font-semibold">Recommended Proof</h2>
            <List items={packet.recommended_projects} empty="No project recommendations generated." />
          </section>
        </aside>
      </section>
    </main>
  );
}

function PacketSection({
  title,
  copy,
  children
}: {
  title: string;
  copy?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="border border-border bg-card p-6">
      <div className="flex items-start justify-between gap-4">
        <h2 className="text-lg font-semibold">{title}</h2>
        {copy ? <CopyButton value={copy} /> : null}
      </div>
      <div className="mt-4">{children}</div>
    </section>
  );
}

function List({ items, empty = "" }: { items: string[]; empty?: string }) {
  if (!items.length) {
    return empty ? <p className="text-sm text-muted-foreground">{empty}</p> : null;
  }
  return (
    <ul className="grid gap-2 text-sm leading-6 text-muted-foreground">
      {items.map((item) => <li key={item}>- {item}</li>)}
    </ul>
  );
}
