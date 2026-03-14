from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.workflow import WorkflowAction


class WorkflowStartRequest(BaseModel):
    workflow_type: str = "standard"
    initial_stage: str = "legal_review"
    approvers: list[dict]


class WorkflowActionRequest(BaseModel):
    comments: str | None = None


class WorkflowEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    workflow_id: int
    user_id: int
    action: WorkflowAction
    comments: str | None
    timestamp: datetime


class WorkflowResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    contract_id: int
    workflow_type: str
    current_stage: str
    approvers: list[dict]
    created_at: datetime
