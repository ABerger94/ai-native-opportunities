import type { Company, Dashboard, Opportunity } from "@/lib/types";

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

export function getOpportunities(): Promise<Opportunity[]> {
  return getJson<Opportunity[]>("/opportunities?limit=50");
}

export function getCompanies(): Promise<Company[]> {
  return getJson<Company[]>("/companies?limit=50");
}
