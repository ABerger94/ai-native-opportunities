import Link from "next/link";
import { ArrowRight, BriefcaseBusiness, Building2, RefreshCw } from "lucide-react";
import { getDashboard } from "@/lib/api";
import { Badge, Score } from "@/components/ui";
import { DashboardActions } from "@/components/dashboard-actions";

export default async function Home() {
  const dashboard = await getDashboard().catch((error: Error) => ({
    top_ai_native_jobs: [],
    trending_companies: [],
    empty_state: {
      has_real_data: false,
      message: `API unavailable: ${error.message}`
    },
    configured_source_count: 0
  }));

  const jobs = dashboard.top_ai_native_jobs;
  const companies = dashboard.trending_companies;

  return (
    <main className="min-h-screen">
      <header className="border-b border-border bg-card">
        <div className="mx-auto flex max-w-7xl flex-col gap-6 px-6 py-6 md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-sm font-medium text-primary">AI-native opportunity intelligence</p>
            <h1 className="mt-1 text-3xl font-semibold tracking-normal">Jobs, contracts, and freelance work where AI is the job</h1>
          </div>
          <DashboardActions />
        </div>
      </header>

      <section className="mx-auto grid max-w-7xl gap-4 px-6 py-6 md:grid-cols-3">
        <Metric icon={<BriefcaseBusiness className="h-5 w-5" />} label="Real Opportunities" value={jobs.length} />
        <Metric icon={<Building2 className="h-5 w-5" />} label="AI Builder Companies" value={companies.length} />
        <Metric icon={<RefreshCw className="h-5 w-5" />} label="Configured Sources" value={dashboard.configured_source_count ?? 0} />
      </section>

      {!dashboard.empty_state.has_real_data ? (
        <section className="mx-auto max-w-7xl px-6">
          <div className="border border-border bg-card p-8">
            <h2 className="text-xl font-semibold">No real source data has been imported yet</h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">
              {dashboard.empty_state.message} Add compliant source definitions in the API source config,
              run ingestion, then upload a resume to calculate matches and gap analyses.
            </p>
          </div>
        </section>
      ) : null}

      <section className="mx-auto grid max-w-7xl gap-6 px-6 py-6 lg:grid-cols-[1.6fr_1fr]">
        <div>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-lg font-semibold">Top AI-Native Opportunities</h2>
            <Badge>Live API data</Badge>
          </div>
          <div className="grid gap-3">
            {jobs.map((job) => (
              <article key={job.id} className="border border-border bg-card p-5">
                <div className="flex flex-col gap-4 md:flex-row md:items-start md:justify-between">
                  <div>
                    <Link className="text-lg font-semibold hover:underline" href={`/opportunities/${job.id}`}>
                      {job.title}
                    </Link>
                    <p className="mt-1 text-sm text-muted-foreground">
                      {job.company?.name ?? job.source} {job.location ? `- ${job.location}` : ""}
                    </p>
                    <div className="mt-3 flex flex-wrap gap-2">
                      <Badge>{job.opportunity_type}</Badge>
                      {job.remote ? <Badge>Remote</Badge> : null}
                      {job.tools_mentioned.slice(0, 5).map((tool) => (
                        <Badge key={tool}>{tool}</Badge>
                      ))}
                    </div>
                    <Link
                      className="mt-4 inline-flex items-center gap-2 text-sm font-medium text-primary hover:underline"
                      href={`/opportunities/${job.id}`}
                    >
                      View opportunity profile <ArrowRight className="h-4 w-4" />
                    </Link>
                  </div>
                  <div className="grid w-full gap-3 md:w-56">
                    <Score label="AI Native" value={job.ai_native_score} />
                    <Score label="Opportunity" value={job.opportunity_score} />
                    <Score label="Freelance AI" value={job.freelance_ai_score} />
                  </div>
                </div>
              </article>
            ))}
          </div>
        </div>

        <aside>
          <div className="mb-3 flex items-center justify-between">
            <h2 className="text-lg font-semibold">AI Builder Index</h2>
            <Badge>Companies</Badge>
          </div>
          <div className="grid gap-3">
            {companies.map((company) => (
              <article key={company.id} className="border border-border bg-card p-5">
                <h3 className="font-semibold">{company.name}</h3>
                <p className="mt-1 text-sm text-muted-foreground">{company.industry ?? "Industry pending from source data"}</p>
                <div className="mt-4 grid gap-3">
                  <Score label="AI Native" value={company.ai_native_score} />
                  <Score label="Company" value={company.company_score} />
                </div>
              </article>
            ))}
          </div>
        </aside>
      </section>
    </main>
  );
}

function Metric({ icon, label, value }: { icon: React.ReactNode; label: string; value: number }) {
  return (
    <div className="border border-border bg-card p-5">
      <div className="flex items-center justify-between text-muted-foreground">
        {icon}
        <span className="text-2xl font-semibold text-foreground">{value}</span>
      </div>
      <p className="mt-3 text-sm font-medium">{label}</p>
    </div>
  );
}
