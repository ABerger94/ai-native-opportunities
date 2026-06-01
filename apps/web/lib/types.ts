export type Opportunity = {
  id: string;
  source: string;
  external_id: string;
  url: string;
  title: string;
  description: string;
  location: string | null;
  remote: boolean;
  opportunity_type: string;
  required_skills: string[];
  preferred_skills: string[];
  tools_mentioned: string[];
  budget_min: number | null;
  budget_max: number | null;
  hourly_min: number | null;
  hourly_max: number | null;
  ai_native_score: number;
  freelance_ai_score: number;
  opportunity_score: number;
  score_explanation: {
    positive_signals?: string[];
    negative_signals?: string[];
    freelance_categories?: string[];
  };
  posted_at: string | null;
  discovered_at: string;
  company: Company | null;
};

export type Company = {
  id: string;
  name: string;
  website_url: string | null;
  careers_url: string | null;
  industry: string | null;
  funding_stage: string | null;
  headcount: string | null;
  remote_policy: string | null;
  tech_stack: string[];
  company_score: number;
  ai_native_score: number;
};

export type Dashboard = {
  top_ai_native_jobs: Opportunity[];
  trending_companies: Company[];
  configured_source_count?: number;
  empty_state: {
    has_real_data: boolean;
    message: string;
  };
};

export type Resume = {
  id: string;
  file_name: string;
  technical_skills: string[];
  business_skills: string[];
  leadership_skills: string[];
  ai_skills: string[];
  automation_skills: string[];
  product_skills: string[];
  startup_skills: string[];
};

export type Match = {
  id: string;
  resume_id: string;
  opportunity_id: string;
  overall_match_score: number;
  skill_match_score: number;
  experience_match_score: number;
  ai_readiness_score: number;
  transition_probability: number;
  fit_band: string;
  missing_skills: string[];
  missing_experience: string[];
  recommended_certifications: string[];
  recommended_projects: string[];
  recommended_portfolio_pieces: string[];
  explanation: {
    positive_signals?: string[];
    needs_improvement?: string[];
    preparation_time?: string;
  };
  opportunity: Opportunity;
};

export type ApplicationPacket = {
  summary: string;
  fit_band: string;
  scores: Record<string, number>;
  pitch: string;
  cover_letter: string;
  resume_focus: string[];
  short_answers: Array<{
    question: string;
    answer: string;
  }>;
  gaps_to_address: string[];
  recommended_projects: string[];
  review_checklist: string[];
};

export type Application = {
  id: string;
  match_id: string;
  status: string;
  packet: ApplicationPacket;
  notes: string | null;
  created_at: string;
  updated_at: string;
  match: Match;
};
