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
export type DataSource = "live" | "researched" | "sample" | "concept" | "mockup";

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
  csm_only: boolean;
  badge: string | null;
  description: string;
  detail: string | null;
  source_url: string | null;
  source_detail: string | null;
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

export type ActionStatus = "queued" | "approved" | "dismissed";

export interface QueuedAction {
  id: string;
  customer_id: string;
  customer_name: string;
  subject: string;
  body: string;
  reasoning: string;
  status: ActionStatus;
  created_at: string;
}

export interface SuccessPlanMetric {
  label: string;
  baseline: number;
  current: number | null;
  target: number;
  due_date: string;
  on_track: boolean;
  progress_pct: number;
}

export interface SuccessPlanChange {
  category: string;
  headline: string;
  detail: string;
  direction: "up" | "down" | "flat";
  data_source: DataSource;
  source_detail: string | null;
}

export interface SuccessPlan {
  customer_id: string;
  customer_name: string;
  domain: string;
  objective: string;
  scope: string;
  high_risk_suppliers: number;
  critical_suppliers: number;
  metric: SuccessPlanMetric;
  owner: string;
  sponsor: string;
  agreed_on: string;
  next_review: string;
  plan_data_source: DataSource;
  plan_source_detail: string;
  summary: string;
  changes: SuccessPlanChange[];
}

export interface PartnerFitReason {
  weight: number;
  text: string;
  source: string;
  tier: "live" | "researched";
}

export interface PartnerFitRow {
  customer_id: string;
  customer_name: string;
  domain: string;
  partner_id: string;
  fit_score: number;
  reasons: PartnerFitReason[];
  recipient_role: string;
  talk_track: string;
  subject: string;
  body: string;
}

export interface PartnerFitBoard {
  generated_at: string;
  partners: { id: string; name: string; sells: string; status: "live" | "upcoming" }[];
  rules: string[];
  rows: PartnerFitRow[];
}

export interface CrTrackerFirm {
  firm: string;
  website: string;
  relationship: string;
  status: string;
  owner: string;
  next_action: string;
  next_action_entries: string[];
  renewal_date: string;
  last_meeting: string;
  days_since: number | null;
  next_meeting?: string;
  frozen: boolean;
}

export interface CrTrackerBoard {
  configured: boolean;
  detail?: string;
  generated_at: string;
  source: string;
  counts: { firms: number; with_meeting_history: number; upcoming_events: number; frozen_excluded: number };
  caveats: string[];
  never_met: CrTrackerFirm[];
  never_met_total: number;
  upcoming: CrTrackerFirm[];
  upcoming_total: number;
  longest_gap: CrTrackerFirm[];
  longest_gap_total: number;
  no_next_action: CrTrackerFirm[];
  no_next_action_total: number;
}
