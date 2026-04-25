from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class PriceSource(str, Enum):
    NADAC = "nadac"
    GOODRX = "goodrx"
    PBM_CVS = "pbm_cvs"
    PBM_ESI = "pbm_esi"
    PBM_OPTUM = "pbm_optum"
    WAC = "wac"
    MEDICAID_REPORT = "medicaid_report"


class SpreadFlag(str, Enum):
    LOW = "LOW"       # < 20%
    MEDIUM = "MEDIUM" # 20-100%
    HIGH = "HIGH"     # 100-500%
    CRITICAL = "CRITICAL"  # > 500%


class Drug(BaseModel):
    ndc: Optional[str] = None
    brand_name: str
    generic_name: Optional[str] = None
    drug_class: Optional[str] = None
    strength: Optional[str] = None
    dosage_form: Optional[str] = None
    quantity: Optional[int] = None


class PricingSnapshot(BaseModel):
    drug_name: str
    ndc: Optional[str] = None
    strength: Optional[str] = None
    quantity: int
    source: PriceSource
    price: float
    price_per_unit: Optional[float] = None
    captured_at: datetime = Field(default_factory=datetime.utcnow)
    pharmacy: Optional[str] = None
    state: Optional[str] = None


class DrugPriceAnalysis(BaseModel):
    drug_name: str
    generic_name: Optional[str] = None
    ndc: Optional[str] = None
    strength: str
    quantity: int
    nadac_total: float
    nadac_per_unit: float
    goodrx_lowest: Optional[float] = None
    plan_price_estimate: Optional[float] = None
    wac: Optional[float] = None
    spread_dollar: float
    spread_pct: float
    flag: SpreadFlag
    pass_through_savings: float
    annual_savings_100_members: float
    medicaid_citation: Optional[str] = None


class DiscrepancyReport(BaseModel):
    report_id: str
    tenant_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    query: str
    summary: str
    drugs: List[DrugPriceAnalysis]
    recommendation: str
    total_annual_savings_100_members: float


class Task(BaseModel):
    task_id: str
    tenant_id: str
    title: str
    description: str
    status: str = "pending"  # pending | running | complete | failed
    progress: int = 0
    current_step: Optional[str] = None
    result_report_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None


class ChatMessage(BaseModel):
    role: str  # user | assistant
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    report: Optional[DiscrepancyReport] = None
    task_id: Optional[str] = None


class Conversation(BaseModel):
    session_id: str
    tenant_id: str
    messages: List[ChatMessage] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ChatRequest(BaseModel):
    message: str
    session_id: str
    history: list = []


class ChatResponse(BaseModel):
    reply: str
    session_id: str
    report: Optional[DiscrepancyReport] = None
    task_id: Optional[str] = None
    task_status: str = "complete"


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    tenant_id: str
