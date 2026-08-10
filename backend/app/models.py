from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class Customer(BaseModel):
    id: str
    name: str
    domain: str
    sponsor: Optional[str] = None
    csm: Optional[str] = None
    notes: Optional[str] = None


class CustomerCreate(BaseModel):
    name: str
    domain: str
    sponsor: Optional[str] = None
    csm: Optional[str] = None
    notes: Optional[str] = None


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    sponsor: Optional[str] = None
    csm: Optional[str] = None
    notes: Optional[str] = None


class ScorePoint(BaseModel):
    date: str
    score: int


class ScoreSummary(BaseModel):
    domain: str
    current_score: Optional[int] = None
    current_grade: Optional[str] = None
    industry: Optional[str] = None
    history: List[ScorePoint] = Field(default_factory=list)
    delta_30d: Optional[int] = None
    delta_182d: Optional[int] = None
    flags: List[str] = Field(default_factory=list)
    error: Optional[str] = None


class UsageIndividual(BaseModel):
    name: str
    visits_7d: int


class UsageSummary(BaseModel):
    is_sample_data: bool = True
    slots_filled_7d: int
    slots_delta_7d: int
    reports_generated_7d: int
    reports_delta_7d: int
    licensed_slots: int
    slots_used: int
    individuals: List[UsageIndividual]
    new_individuals: List[str] = Field(default_factory=list)


class DecisionMaker(BaseModel):
    name: str
    title: str
    linkedin_url: Optional[str] = None
    primary_focus: str
    is_ciso_or_biso: bool = False
    status: Literal["new", "existing"] = "existing"


class DecisionMakerImport(BaseModel):
    people: List[DecisionMaker]


class DecisionMakerImportRequest(BaseModel):
    """Either raw pasted text (parsed server-side) or an already-structured people list."""

    text: Optional[str] = None
    people: Optional[List[DecisionMaker]] = None


class DecisionMakerRecord(BaseModel):
    domain: str
    imported_at: Optional[str] = None
    people: List[DecisionMaker] = Field(default_factory=list)


NewsEventType = Literal["acquisition", "new_office", "product_launch"]


class NewsEvent(BaseModel):
    event_type: NewsEventType
    headline: str
    date: str
    summary: str
    source_url: Optional[str] = None


class NewsEventsImportRequest(BaseModel):
    """Either raw pasted text (parsed server-side) or an already-structured events list."""

    text: Optional[str] = None
    events: Optional[List[NewsEvent]] = None


class NewsRecord(BaseModel):
    domain: str
    imported_at: Optional[str] = None
    events: List[NewsEvent] = Field(default_factory=list)


SignalLevel = Literal["upsell", "retention_risk", "neutral"]


class Signal(BaseModel):
    customer_id: str
    level: SignalLevel
    priority: int
    reasons: List[str]


class CustomerOverview(BaseModel):
    customer: Customer
    score: ScoreSummary
    usage: UsageSummary
    decision_makers: DecisionMakerRecord
    news: NewsRecord
    signal: Signal


class CustomerSummary(BaseModel):
    """Lightweight row for the main dashboard table (no full score history)."""

    customer: Customer
    current_score: Optional[int] = None
    current_grade: Optional[str] = None
    score_error: Optional[str] = None
    delta_30d: Optional[int] = None
    usage: UsageSummary
    decision_maker_count: int
    signal: Signal


OpportunityGroup = Literal["proof", "adoption", "expansion", "engagement"]
Sentiment = Literal["good", "watch", "info"]
# "live"    = derived from a real external source (SSC API, imported research)
# "sample"  = real trigger logic, placeholder input data (the usage generator)
# "concept" = the trigger isn't built; an illustration of what it would surface once
#             the underlying data source exists. Hidden unless explicitly requested.
DataSource = Literal["live", "sample", "concept"]


class RecipientOption(BaseModel):
    name: str
    role: str


class OpportunityCard(BaseModel):
    card_id: str
    group: OpportunityGroup
    customer_id: str
    customer_name: str
    industry: Optional[str] = None
    value: str
    label: str
    sentiment: Sentiment
    data_source: DataSource = "live"
    # For concept cards: which trigger from the brief this illustrates, e.g. "#9".
    concept_trigger: Optional[str] = None
    badge: Optional[str] = None
    description: str
    # Short (<=2 line) active-voice instruction shown on the card face. `detail` carries
    # the fuller explanation, shown on demand (hover/click) rather than by default.
    detail: Optional[str] = None
    detected_at: str
    recipient_name: str
    recipient_role: str
    # Everyone we know of at this customer, so a CSM can redirect the draft without
    # leaving the dashboard.
    recipient_options: List[RecipientOption] = Field(default_factory=list)
    subject: str
    body: str


class AccountChip(BaseModel):
    customer_id: str
    customer_name: str
    domain: str
    industry: Optional[str] = None
    score: Optional[int] = None
    grade: Optional[str] = None
    sentiment: Sentiment
    open_opportunities: int


class OpportunityBoardResponse(BaseModel):
    chips: List[AccountChip]
    cards: List[OpportunityCard]
