from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.contract import ContractStatus, ContractType


class ContractBase(BaseModel):
    title: str
    contract_type: ContractType
    vendor_name: str | None = None
    amount: Decimal | None = None
    start_date: date | None = None
    end_date: date | None = None
    metadata: dict | None = None
    file_path: str | None = None
    assigned_to: int | None = None


class ContractCreate(ContractBase):
    pass


class ContractUpdate(BaseModel):
    title: str | None = None
    status: ContractStatus | None = None
    vendor_name: str | None = None
    amount: Decimal | None = None
    start_date: date | None = None
    end_date: date | None = None
    metadata: dict | None = None
    file_path: str | None = None
    assigned_to: int | None = None


class ContractResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    contract_number: str
    title: str
    status: ContractStatus
    contract_type: ContractType
    vendor_name: str | None
    amount: Decimal | None
    start_date: date | None
    end_date: date | None
    created_by: int | None
    assigned_to: int | None
    metadata_json: dict | None = Field(default=None, alias="metadata")
    file_path: str | None
    created_at: datetime
    updated_at: datetime


class ContractListResponse(BaseModel):
    items: list[ContractResponse]
    total: int
    page: int
    limit: int


class ContractSearchRequest(BaseModel):
    query: str
