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
    individuals: List[UsageIndividual]


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
