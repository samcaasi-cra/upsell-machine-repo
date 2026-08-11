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
  industry: string | null;
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
  licensed_slots: number;
  slots_used: number;
  individuals: UsageIndividual[];
  new_individuals: string[];
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

export type NewsEventType = "acquisition" | "new_office" | "product_launch";

export interface NewsEvent {
  event_type: NewsEventType;
  headline: string;
  date: string;
  summary: string;
  source_url: string | null;
}

export interface NewsRecord {
  domain: string;
  imported_at: string | null;
  events: NewsEvent[];
}

export interface CustomerOverview {
  customer: Customer;
  score: ScoreSummary;
  usage: UsageSummary;
  decision_makers: DecisionMakerRecord;
  news: NewsRecord;
  signal: Signal;
}

export type OpportunityGroup = "proof" | "adoption" | "expansion" | "engagement";
export type Sentiment = "good" | "watch" | "info";
export type DataSource = "live" | "researched" | "sample" | "concept";

export interface OpportunityCard {
  card_id: string;
  group: OpportunityGroup;
  customer_id: string;
  customer_name: string;
  industry: string | null;
  value: string;
  label: string;
  sentiment: Sentiment;
  data_source: DataSource;
  concept_trigger: string | null;
  badge: string | null;
  description: string;
  detail: string | null;
  source_url: string | null;
  detected_at: string;
  recipient_name: string;
  recipient_role: string;
  recipient_options: RecipientOption[];
  subject: string;
  body: string;
}

export interface RecipientOption {
  name: string;
  role: string;
}

export interface AccountChip {
  customer_id: string;
  customer_name: string;
  domain: string;
  industry: string | null;
  score: number | null;
  grade: string | null;
  sentiment: Sentiment;
  open_opportunities: number;
}

export interface OpportunityBoardResponse {
  chips: AccountChip[];
  cards: OpportunityCard[];
}
