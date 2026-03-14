from pydantic import BaseModel, Field


class SpendAnalyticsResponse(BaseModel):
    vendor: str | None = None
    year: int | None = None
    total_contracts: int
    total_spend: float
    average_contract_value: float


class CustomReportRequest(BaseModel):
    group_by: str = Field(default="status")
    metric: str = Field(default="count")
    year: int | None = None


class CustomReportItem(BaseModel):
    key: str
    value: float


class CustomReportResponse(BaseModel):
    group_by: str
    metric: str
    items: list[CustomReportItem]
