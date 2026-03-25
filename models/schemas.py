from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime
from enum import Enum


class ServiceLine(str, Enum):
    FERTILITY = "fertility"
    MENOPAUSE = "menopause"
    MATERNAL_MENTAL_HEALTH = "maternal_mental_health"
    PCOS = "pcos"
    ENDOMETRIOSIS = "endometriosis"
    PELVIC_FLOOR = "pelvic_floor"
    GYNECOLOGY = "gynecology"
    MATERNAL_FETAL = "maternal_fetal"


class EngagementMode(str, Enum):
    FEASIBILITY = "feasibility"
    PERFORMANCE = "performance"


class InvestorRiskRating(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    SPECULATIVE = "speculative"


class CoverageStatus(str, Enum):
    COVERED = "covered"
    COVERED_WITH_RESTRICTIONS = "covered_with_restrictions"
    UNLABELED_USE = "unlabeled_use"
    NO_PATHWAY = "no_pathway"
    STATE_MANDATE_ONLY = "state_mandate_only"


class EngagementRequest(BaseModel):
    company_name: str
    service_lines: list[ServiceLine]
    target_payers: list[str] = Field(default_factory=list)
    geography: list[str] = Field(description="State abbreviations, e.g. ['CA','TX']")
    engagement_mode: EngagementMode

    # feasibility mode
    service_description: Optional[str] = None
    target_cpt_codes: Optional[list[str]] = None

    # performance mode
    fundraise_stage: Optional[Literal["series_a", "series_b"]] = None


class CPTCodeEntry(BaseModel):
    code: str
    descriptor: str
    coverage_status: CoverageStatus
    payer_notes: Optional[str] = None
    rvu: Optional[float] = None
    medicare_allowed_amount: Optional[float] = None


class PathwayMilestone(BaseModel):
    step: int
    title: str
    description: str
    estimated_timeline: str
    dependency: Optional[str] = None


class GapAnalysis(BaseModel):
    uncompensated_service_volume_estimate: Optional[int] = None
    avg_allowed_amount_per_encounter: Optional[float] = None
    estimated_annual_revenue_gap: Optional[float] = None
    gap_narrative: str


class ReimbursementPathwayReport(BaseModel):
    company_name: str
    service_lines: list[ServiceLine]
    engagement_mode: EngagementMode

    current_reimbursement_status: dict[str, CoverageStatus]
    cpt_landscape: list[CPTCodeEntry]
    gap_quantification: GapAnalysis
    pathway_milestones: list[PathwayMilestone]
    comparable_precedents: list[str]
    payer_strategy_recommendations: list[str]

    investor_risk_rating: InvestorRiskRating
    investor_executive_summary: str
    investor_status_summary: str
    investor_pathway_narrative: str

    data_sources: list[str]
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    confidence_score: float = Field(ge=0.0, le=1.0)


class AgentState(BaseModel):
    request: EngagementRequest
    cpt_landscape: list[CPTCodeEntry] = Field(default_factory=list)
    policy_findings: dict = Field(default_factory=dict)
    gap_analysis: Optional[GapAnalysis] = None
    report: Optional[ReimbursementPathwayReport] = None
    requires_human_review: bool = False
    escalation_reason: Optional[str] = None
    errors: list[str] = Field(default_factory=list)
