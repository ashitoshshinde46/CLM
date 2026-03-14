from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user
from app.models.contract import Contract, ContractStatus
from app.models.user import User
from app.models.workflow import Workflow, WorkflowAction, WorkflowEvent
from app.schemas.common import MessageResponse
from app.schemas.workflow import WorkflowActionRequest, WorkflowResponse, WorkflowStartRequest

router = APIRouter(prefix="/workflows", tags=["Workflows"])


@router.post("/{contract_id}/start", response_model=WorkflowResponse, status_code=status.HTTP_201_CREATED)
def start_workflow(
    contract_id: int,
    payload: WorkflowStartRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> WorkflowResponse:
    contract = db.scalar(select(Contract).where(Contract.id == contract_id, Contract.status != ContractStatus.deleted))
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")

    existing = db.scalar(select(Workflow).where(Workflow.contract_id == contract_id))
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Workflow already exists")

    workflow = Workflow(
        contract_id=contract_id,
        workflow_type=payload.workflow_type,
        current_stage=payload.initial_stage,
        approvers=payload.approvers,
    )
    db.add(workflow)
    db.commit()
    db.refresh(workflow)
    return WorkflowResponse.model_validate(workflow)


@router.get("/{contract_id}", response_model=WorkflowResponse)
def get_workflow(
    contract_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> WorkflowResponse:
    workflow = db.scalar(select(Workflow).where(Workflow.contract_id == contract_id))
    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    return WorkflowResponse.model_validate(workflow)


def _apply_action(workflow: Workflow, user_id: int, action: WorkflowAction) -> None:
    for approver in workflow.approvers:
        if approver.get("user_id") == user_id and approver.get("status") == "pending":
            approver["status"] = "approved" if action == WorkflowAction.approve else "rejected"
            break

    pending = [a for a in workflow.approvers if a.get("status") == "pending"]
    if action == WorkflowAction.reject:
        workflow.current_stage = "rejected"
    elif pending:
        workflow.current_stage = pending[0].get("stage", "in_review")
    else:
        workflow.current_stage = "completed"


@router.post("/{workflow_id}/approve", response_model=MessageResponse)
def approve(
    workflow_id: int,
    payload: WorkflowActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    workflow = db.scalar(select(Workflow).where(Workflow.id == workflow_id))
    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    authorized = any(
        approver.get("user_id") == current_user.id and approver.get("status") == "pending"
        for approver in workflow.approvers
    )
    if not authorized:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No pending approval for user")

    _apply_action(workflow, current_user.id, WorkflowAction.approve)
    db.add(
        WorkflowEvent(
            workflow_id=workflow.id,
            user_id=current_user.id,
            action=WorkflowAction.approve,
            comments=payload.comments,
        )
    )
    db.commit()
    return MessageResponse(message="Stage approved")


@router.post("/{workflow_id}/reject", response_model=MessageResponse)
def reject(
    workflow_id: int,
    payload: WorkflowActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> MessageResponse:
    workflow = db.scalar(select(Workflow).where(Workflow.id == workflow_id))
    if not workflow:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

    authorized = any(
        approver.get("user_id") == current_user.id and approver.get("status") == "pending"
        for approver in workflow.approvers
    )
    if not authorized:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="No pending approval for user")

    _apply_action(workflow, current_user.id, WorkflowAction.reject)
    db.add(
        WorkflowEvent(
            workflow_id=workflow.id,
            user_id=current_user.id,
            action=WorkflowAction.reject,
            comments=payload.comments,
        )
    )
    db.commit()
    return MessageResponse(message="Workflow rejected")


@router.get("/my-tasks/list", response_model=list[WorkflowResponse])
def my_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[WorkflowResponse]:
    workflows = db.scalars(
        select(Workflow).where(
            and_(
                Workflow.current_stage != "completed",
                Workflow.current_stage != "rejected",
                or_(
                    Workflow.approvers.contains([{"user_id": current_user.id, "status": "pending"}]),
                    Workflow.approvers.contains([{"user_id": current_user.id}]),
                ),
            )
        )
    ).all()

    pending_for_user = [
        wf
        for wf in workflows
        if any(a.get("user_id") == current_user.id and a.get("status") == "pending" for a in wf.approvers)
    ]
    return [WorkflowResponse.model_validate(item) for item in pending_for_user]
