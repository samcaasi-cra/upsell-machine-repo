export interface Customer {
  id: string;
  name: string;
  domain: string;
  sponsor: string | null;
  csm: string | null;
  notes: string | null;
}

export interface CustomerCreate {
  name: string;
  domain: string;
  sponsor?: string | null;
  csm?: string | null;
  notes?: string | null;
}

export interface ScorePoint {
  date: string;
  score: number;
}

export interface ScoreSummary {
  domain: string;
  current_score: number | null;
  current_grade: string | null;
  history: ScorePoint[];
  delta_30d: number | null;
  delta_182d: number | null;
  flags: string[];
  error: string | null;
}

export interface UsageIndividual {
  name: string;
  visits_7d: number;
}

export interface UsageSummary {
  is_sample_data: boolean;
  slots_filled_7d: number;
  slots_delta_7d: number;
  reports_generated_7d: number;
  reports_delta_7d: number;
  individuals: UsageIndividual[];
}

export interface DecisionMaker {
  name: string;
  title: string;
  linkedin_url: string | null;
  primary_focus: string;
  is_ciso_or_biso: boolean;
  status: "new" | "existing";
}

export interface DecisionMakerRecord {
  domain: string;
  imported_at: string | null;
  people: DecisionMaker[];
}

export type SignalLevel = "upsell" | "retention_risk" | "neutral";

export interface Signal {
  customer_id: string;
  level: SignalLevel;
  priority: number;
  reasons: string[];
}

export interface CustomerSummary {
  customer: Customer;
  current_score: number | null;
  current_grade: string | null;
  score_error: string | null;
  delta_30d: number | null;
  usage: UsageSummary;
  decision_maker_count: number;
  signal: Signal;
}

export interface CustomerOverview {
  customer: Customer;
  score: ScoreSummary;
  usage: UsageSummary;
  decision_makers: DecisionMakerRecord;
  signal: Signal;
}
