export type Opportunity = {
  id: string;
  source: string;
  url: string;
  title: string;
  description: string;
  location: string | null;
  remote: boolean;
  opportunity_type: string;
  required_skills: string[];
  preferred_skills: string[];
  tools_mentioned: string[];
  ai_native_score: number;
  freelance_ai_score: number;
  opportunity_score: number;
  score_explanation: {
    positive_signals?: string[];
    negative_signals?: string[];
    freelance_categories?: string[];
  };
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
  empty_state: {
    has_real_data: boolean;
    message: string;
  };
};
