from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class RiskAssessmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    contract_id: int
    risk_score: Decimal
    high_risk_clauses: list[dict] | None
    compliance_status: str
    assessed_by: int | None
    assessed_at: datetime


class RiskDashboardItem(BaseModel):
    grouping_key: str
    total_contracts: int
    average_risk_score: float


class RiskDashboardResponse(BaseModel):
    by_vendor: list[RiskDashboardItem]
    by_type: list[RiskDashboardItem]
