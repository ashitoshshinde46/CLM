from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user
from app.models.contract import Contract, ContractStatus
from app.models.obligation import Obligation, ObligationStatus
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.obligation import ObligationCreate, ObligationResponse, ObligationUpdate

router = APIRouter(prefix="/obligations", tags=["Obligation Management"])


def _normalize_status(obligation: Obligation) -> None:
    if obligation.status == ObligationStatus.completed:
        return
    if obligation.due_date and obligation.due_date < date.today():
        obligation.status = ObligationStatus.overdue
    else:
        obligation.status = ObligationStatus.pending


@router.get("", response_model=list[ObligationResponse])
def list_obligations(
    status_filter: ObligationStatus | None = Query(None, alias="status"),
    due_before: date | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[ObligationResponse]:
    query = select(Obligation)
    if status_filter:
        query = query.where(Obligation.status == status_filter)
    if due_before:
        query = query.where(Obligation.due_date <= due_before)

    obligations = db.scalars(query.order_by(Obligation.due_date.asc().nulls_last(), Obligation.id.desc())).all()
    for item in obligations:
        _normalize_status(item)
    db.commit()
    return [ObligationResponse.model_validate(item) for item in obligations]


@router.post("", response_model=ObligationResponse, status_code=status.HTTP_201_CREATED)
def create_obligation(
    payload: ObligationCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ObligationResponse:
    contract = db.scalar(
        select(Contract).where(
            and_(
                Contract.id == payload.contract_id,
                Contract.status != ContractStatus.deleted,
            )
        )
    )
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")

    obligation = Obligation(
        contract_id=payload.contract_id,
        description=payload.description,
        due_date=payload.due_date,
        responsible_user=payload.responsible_user,
        recurrence=payload.recurrence,
    )
    _normalize_status(obligation)
    db.add(obligation)
    db.commit()
    db.refresh(obligation)
    return ObligationResponse.model_validate(obligation)


@router.put("/{obligation_id}/complete", response_model=MessageResponse)
def mark_complete(
    obligation_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> MessageResponse:
    obligation = db.scalar(select(Obligation).where(Obligation.id == obligation_id))
    if not obligation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Obligation not found")

    obligation.status = ObligationStatus.completed
    db.commit()
    return MessageResponse(message="Obligation marked as completed")


@router.put("/{obligation_id}", response_model=ObligationResponse)
def update_obligation(
    obligation_id: int,
    payload: ObligationUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ObligationResponse:
    obligation = db.scalar(select(Obligation).where(Obligation.id == obligation_id))
    if not obligation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Obligation not found")

    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(obligation, key, value)

    _normalize_status(obligation)
    db.commit()
    db.refresh(obligation)
    return ObligationResponse.model_validate(obligation)


@router.delete("/{obligation_id}", response_model=MessageResponse)
def delete_obligation(
    obligation_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> MessageResponse:
    obligation = db.scalar(select(Obligation).where(Obligation.id == obligation_id))
    if not obligation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Obligation not found")

    db.delete(obligation)
    db.commit()
    return MessageResponse(message="Obligation deleted")


@router.get("/contract/{contract_id}", response_model=list[ObligationResponse])
def list_contract_obligations(
    contract_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[ObligationResponse]:
    contract = db.scalar(select(Contract).where(Contract.id == contract_id, Contract.status != ContractStatus.deleted))
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")

    obligations = db.scalars(select(Obligation).where(Obligation.contract_id == contract_id).order_by(Obligation.id.desc())).all()
    for item in obligations:
        _normalize_status(item)
    db.commit()
    return [ObligationResponse.model_validate(item) for item in obligations]
