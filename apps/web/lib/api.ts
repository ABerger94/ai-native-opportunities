import type { Application, Company, Dashboard, Match, Opportunity } from "@/lib/types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    cache: "no-store",
    headers: { Accept: "application/json" }
  });
  if (!response.ok) {
    throw new Error(`API request failed: ${response.status} ${response.statusText}`);
  }
  return response.json() as Promise<T>;
}

export function getDashboard(): Promise<Dashboard> {
  return getJson<Dashboard>("/dashboard");
}

export function getOpportunities(params: Record<string, string | number | boolean | undefined> = {}): Promise<Opportunity[]> {
  const query = new URLSearchParams();
  for (const [key, value] of Object.entries({ limit: 50, ...params })) {
    const normalized = value === undefined ? "" : String(value);
    if (normalized !== "") {
      query.set(key, normalized);
    }
  }
  return getJson<Opportunity[]>(`/opportunities?${query.toString()}`);
}

export function getOpportunity(id: string): Promise<Opportunity> {
  return getJson<Opportunity>(`/opportunities/${id}`);
}

export function getCompanies(): Promise<Company[]> {
  return getJson<Company[]>("/companies?limit=50");
}

export function getMatchReport(id: string): Promise<Match> {
  return getJson<Match>(`/match-reports/${id}`);
}

export function getApplication(id: string): Promise<Application> {
  return getJson<Application>(`/applications/${id}`);
}

export function getApplications(): Promise<Application[]> {
  return getJson<Application[]>("/applications?limit=50");
}
