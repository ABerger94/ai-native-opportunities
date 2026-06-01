import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { getApplications } from "@/lib/api";
import { Badge, Score } from "@/components/ui";

export async function ApplicationTracker() {
  const applications = await getApplications().catch(() => []);

  if (!applications.length) {
    return (
      <section className="mx-auto max-w-7xl px-6 pb-6">
        <div className="border border-border bg-card p-5">
          <p className="text-sm font-medium text-primary">Application Agent</p>
          <h2 className="mt-1 text-xl font-semibold">No application packets yet</h2>
          <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
            Upload a resume, review your ranked matches, then build an application packet for roles you want to pursue.
          </p>
        </div>
      </section>
    );
  }

  return (
    <section className="mx-auto max-w-7xl px-6 pb-6">
      <div className="border border-border bg-card p-5">
        <div className="mb-4 flex items-center justify-between gap-4">
          <div>
            <p className="text-sm font-medium text-primary">Application Agent</p>
            <h2 className="mt-1 text-xl font-semibold">Application Tracker</h2>
          </div>
          <Badge>{applications.length} packets</Badge>
        </div>
        <div className="grid gap-3">
          {applications.slice(0, 8).map((application) => {
            const opportunity = application.match.opportunity;
            return (
              <article key={application.id} className="border border-border bg-background p-4">
                <div className="grid gap-4 lg:grid-cols-[1fr_260px]">
                  <div>
                    <div className="flex flex-wrap gap-2">
                      <Badge>{application.status.replaceAll("_", " ")}</Badge>
                      <Badge>{application.match.fit_band.replaceAll("_", " ")}</Badge>
                    </div>
                    <Link className="mt-3 block text-lg font-semibold hover:underline" href={`/applications/${application.id}`}>
                      {opportunity.title}
                    </Link>
                    <p className="mt-1 text-sm text-muted-foreground">
                      {opportunity.company?.name ?? opportunity.source}
                      {opportunity.location ? ` - ${opportunity.location}` : ""}
                    </p>
                    <Link
                      className="mt-3 inline-flex items-center gap-2 text-sm font-medium text-primary hover:underline"
                      href={`/applications/${application.id}`}
                    >
                      Continue workflow <ArrowRight className="h-4 w-4" />
                    </Link>
                  </div>
                  <div className="grid content-start gap-3">
                    <Score label="Overall Match" value={application.match.overall_match_score} />
                    <Score label="AI Readiness" value={application.match.ai_readiness_score} />
                  </div>
                </div>
              </article>
            );
          })}
        </div>
      </div>
    </section>
  );
}
