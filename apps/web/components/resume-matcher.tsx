"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { ArrowRight, FileUp, RefreshCw } from "lucide-react";
import { Badge, Button, Score } from "@/components/ui";
import { CreateApplicationButton } from "@/components/application-actions";
import type { Match, Resume } from "@/lib/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const STORAGE_KEY = "ai-native-latest-resume-id";

export function ResumeMatcher() {
  const fileRef = useRef<HTMLInputElement>(null);
  const [resume, setResume] = useState<Resume | null>(null);
  const [matches, setMatches] = useState<Match[]>([]);
  const [status, setStatus] = useState("Upload a resume to see ranked remote and hybrid opportunity matches.");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const resumeId = window.localStorage.getItem(STORAGE_KEY);
    if (!resumeId) {
      return;
    }
    setStatus("Loading your latest match results...");
    void loadMatches(resumeId);
  }, []);

  async function loadMatches(resumeId: string) {
    try {
      const response = await fetch(`${API_BASE_URL}/matches/${resumeId}?limit=12`, {
        headers: { Accept: "application/json" }
      });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      const result = (await response.json()) as Match[];
      setMatches(result);
      setStatus(result.length ? "Showing your latest resume-to-opportunity matches." : "No matches calculated yet.");
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Could not load previous matches.");
    }
  }

  async function uploadResume(file: File | undefined) {
    if (!file) {
      return;
    }
    setBusy(true);
    setMatches([]);
    setStatus("Uploading resume and extracting skills...");
    const form = new FormData();
    form.append("file", file);
    try {
      const uploadResponse = await fetch(`${API_BASE_URL}/resumes?local_user_id=local-user`, {
        method: "POST",
        body: form
      });
      if (!uploadResponse.ok) {
        throw new Error(await uploadResponse.text());
      }
      const uploadedResume = (await uploadResponse.json()) as Resume;
      setResume(uploadedResume);
      window.localStorage.setItem(STORAGE_KEY, uploadedResume.id);

      setStatus("Calculating match scores across imported remote and hybrid opportunities...");
      const matchResponse = await fetch(`${API_BASE_URL}/resumes/${uploadedResume.id}/match?limit=12`, {
        method: "POST",
        headers: { Accept: "application/json" }
      });
      if (!matchResponse.ok) {
        throw new Error(await matchResponse.text());
      }
      const result = (await matchResponse.json()) as Match[];
      setMatches(result);
      setStatus(`Matched ${uploadedResume.file_name} against the live opportunity database.`);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Resume matching failed.");
    } finally {
      setBusy(false);
      if (fileRef.current) {
        fileRef.current.value = "";
      }
    }
  }

  const skills = resume
    ? [
        ...resume.ai_skills,
        ...resume.automation_skills,
        ...resume.product_skills,
        ...resume.business_skills,
        ...resume.leadership_skills,
        ...resume.technical_skills,
        ...resume.startup_skills
      ].slice(0, 12)
    : [];

  return (
    <section className="mx-auto max-w-7xl px-6 pb-6">
      <div className="border border-border bg-card p-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p className="text-sm font-medium text-primary">Resume Match Results</p>
            <h2 className="mt-1 text-xl font-semibold">See how your resume compares to live remote and hybrid AI-native opportunities</h2>
            <p className="mt-2 max-w-3xl text-sm leading-6 text-muted-foreground">{status}</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <input
              ref={fileRef}
              className="hidden"
              type="file"
              accept=".pdf,.docx,.txt"
              onChange={(event) => void uploadResume(event.target.files?.[0])}
            />
            <Button disabled={busy} onClick={() => fileRef.current?.click()}>
              <FileUp className="mr-2 h-4 w-4" />
              Upload Resume
            </Button>
            {matches.length ? (
              <Button disabled={busy} className="bg-foreground" onClick={() => void loadMatches(matches[0].resume_id)}>
                <RefreshCw className="mr-2 h-4 w-4" />
                Refresh Matches
              </Button>
            ) : null}
          </div>
        </div>

        {skills.length ? (
          <div className="mt-4 flex flex-wrap gap-2">
            {skills.map((skill) => <Badge key={skill}>{skill}</Badge>)}
          </div>
        ) : null}

        {matches.length ? (
          <div className="mt-5 grid gap-3">
            {matches.map((match) => (
              <article key={match.id} className="border border-border bg-background p-4">
                <div className="grid gap-4 lg:grid-cols-[1fr_300px]">
                  <div>
                    <div className="flex flex-wrap gap-2">
                      <Badge>{formatFitBand(match.fit_band)}</Badge>
                      <Badge>{match.opportunity.opportunity_type}</Badge>
                      {match.explanation.preparation_time ? <Badge>{match.explanation.preparation_time}</Badge> : null}
                    </div>
                    <Link className="mt-3 block text-lg font-semibold hover:underline" href={`/opportunities/${match.opportunity.id}`}>
                      {match.opportunity.title}
                    </Link>
                    <p className="mt-1 text-sm text-muted-foreground">
                      {match.opportunity.company?.name ?? match.opportunity.source}
                      {match.opportunity.location ? ` - ${match.opportunity.location}` : ""}
                    </p>
                    <MatchList label="Strong alignment" items={match.explanation.positive_signals ?? []} />
                    <MatchList label="Gaps to close" items={[...match.missing_skills, ...match.missing_experience].slice(0, 6)} />
                    <MatchList label="Recommended projects" items={match.recommended_projects} />
                    <div className="mt-4 flex flex-wrap gap-4">
                      <CreateApplicationButton matchId={match.id} />
                      <Link
                        className="inline-flex items-center gap-2 text-sm font-medium text-primary hover:underline"
                        href={`/matches/${match.id}`}
                      >
                        View capability report <ArrowRight className="h-4 w-4" />
                      </Link>
                      <Link
                        className="inline-flex items-center gap-2 text-sm font-medium text-muted-foreground hover:text-foreground hover:underline"
                        href={`/opportunities/${match.opportunity.id}`}
                      >
                        Open opportunity profile <ArrowRight className="h-4 w-4" />
                      </Link>
                    </div>
                  </div>
                  <div className="grid content-start gap-3">
                    <Score label="Overall Match" value={match.overall_match_score} />
                    <Score label="Skill Match" value={match.skill_match_score} />
                    <Score label="Experience" value={match.experience_match_score} />
                    <Score label="AI Readiness" value={match.ai_readiness_score} />
                    <Score label="Transition Probability" value={match.transition_probability} />
                  </div>
                </div>
              </article>
            ))}
          </div>
        ) : null}
      </div>
    </section>
  );
}

function MatchList({ label, items }: { label: string; items: string[] }) {
  if (!items.length) {
    return null;
  }
  return (
    <div className="mt-3">
      <h3 className="text-sm font-semibold">{label}</h3>
      <div className="mt-2 flex flex-wrap gap-2">
        {items.slice(0, 8).map((item) => <Badge key={item}>{item}</Badge>)}
      </div>
    </div>
  );
}

function formatFitBand(value: string) {
  return value.replaceAll("_", " ");
}
