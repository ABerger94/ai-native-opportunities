"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { ArrowRight, RefreshCw } from "lucide-react";
import { Badge, Button, Score } from "@/components/ui";
import { CreateApplicationButton } from "@/components/application-actions";
import type { Match } from "@/lib/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const STORAGE_KEY = "ai-native-latest-resume-id";

export function OpportunityMatchPanel({ opportunityId }: { opportunityId: string }) {
  const [match, setMatch] = useState<Match | null>(null);
  const [status, setStatus] = useState("Upload a resume from the dashboard to analyze this role.");
  const [busy, setBusy] = useState(false);

  const analyze = useCallback(async (resumeId?: string | null) => {
    const activeResumeId = resumeId ?? window.localStorage.getItem(STORAGE_KEY);
    if (!activeResumeId) {
      setStatus("No resume found yet. Upload a resume from the dashboard, then return to this profile.");
      return;
    }
    setBusy(true);
    setStatus("Analyzing this opportunity against your latest resume...");
    try {
      const response = await fetch(
        `${API_BASE_URL}/resumes/${activeResumeId}/opportunities/${opportunityId}/match`,
        { headers: { Accept: "application/json" } }
      );
      if (!response.ok) {
        throw new Error(await response.text());
      }
      const result = (await response.json()) as Match;
      setMatch(result);
      setStatus("Capability match loaded for your latest resume.");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Could not analyze this role.");
    } finally {
      setBusy(false);
    }
  }, [opportunityId]);

  useEffect(() => {
    const resumeId = window.localStorage.getItem(STORAGE_KEY);
    if (!resumeId) {
      return;
    }
    void analyze(resumeId);
  }, [analyze]);

  return (
    <section className="border border-border bg-card p-5">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold">Your Match</h2>
          <p className="mt-1 text-sm leading-6 text-muted-foreground">{status}</p>
        </div>
        <Button disabled={busy} className="h-9 bg-foreground px-3" onClick={() => void analyze()}>
          <RefreshCw className="mr-2 h-4 w-4" />
          Analyze
        </Button>
      </div>

      {match ? (
        <div className="mt-5 grid gap-4">
          <div className="flex flex-wrap gap-2">
            <Badge>{match.fit_band.replaceAll("_", " ")}</Badge>
            {match.explanation.preparation_time ? <Badge>{match.explanation.preparation_time}</Badge> : null}
          </div>
          <div className="grid gap-4">
            <Score label="Overall Match" value={match.overall_match_score} />
            <Score label="Skill Match" value={match.skill_match_score} />
            <Score label="Experience" value={match.experience_match_score} />
            <Score label="AI Readiness" value={match.ai_readiness_score} />
            <Score label="Transition Probability" value={match.transition_probability} />
          </div>

          <PanelList label="Strong alignment" items={match.explanation.positive_signals ?? []} />
          <PanelList label="Gaps to close" items={[...match.missing_skills, ...match.missing_experience].slice(0, 8)} />
          <PanelList label="Recommended projects" items={match.recommended_projects} />

          <div className="flex flex-wrap gap-3">
            <CreateApplicationButton matchId={match.id} />
            <Link
              className="inline-flex h-10 items-center justify-center gap-2 rounded-md border border-border px-4 text-sm font-medium transition hover:bg-muted"
              href={`/matches/${match.id}`}
            >
              Capability report <ArrowRight className="h-4 w-4" />
            </Link>
          </div>
        </div>
      ) : null}
    </section>
  );
}

function PanelList({ label, items }: { label: string; items: string[] }) {
  if (!items.length) {
    return null;
  }
  return (
    <div>
      <h3 className="text-sm font-semibold">{label}</h3>
      <div className="mt-2 flex flex-wrap gap-2">
        {items.slice(0, 8).map((item) => <Badge key={item}>{item}</Badge>)}
      </div>
    </div>
  );
}
