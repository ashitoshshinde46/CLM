from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.obligation import ObligationStatus


class ObligationCreate(BaseModel):
    contract_id: int
    description: str
    due_date: date | None = None
    responsible_user: int | None = None
    recurrence: str | None = None


class ObligationUpdate(BaseModel):
    description: str | None = None
    due_date: date | None = None
    responsible_user: int | None = None
    recurrence: str | None = None
    status: ObligationStatus | None = None


class ObligationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    contract_id: int
    description: str
    due_date: date | None
    responsible_user: int | None
    status: ObligationStatus
    recurrence: str | None
    created_at: datetime
