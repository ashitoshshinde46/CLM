from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user
from app.models.contract import Contract, ContractStatus
from app.models.user import User
from app.schemas.contract import (
    ContractCreate,
    ContractListResponse,
    ContractResponse,
    ContractSearchRequest,
    ContractUpdate,
)
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/contracts", tags=["Contracts"])


def _generate_contract_number(db: Session) -> str:
    today = datetime.utcnow().strftime("%Y%m%d")
    count = db.scalar(select(func.count(Contract.id))) or 0
    return f"CLM-{today}-{count + 1:05d}"


@router.get("", response_model=ContractListResponse)
def list_contracts(
    status_filter: ContractStatus | None = Query(None, alias="status"),
    vendor: str | None = None,
    type_filter: str | None = Query(None, alias="type"),
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ContractListResponse:
    filters = [Contract.status != ContractStatus.deleted]
    if status_filter:
        filters.append(Contract.status == status_filter)
    if vendor:
        filters.append(Contract.vendor_name.ilike(f"%{vendor}%"))
    if type_filter:
        filters.append(Contract.contract_type == type_filter)

    query = select(Contract).where(and_(*filters)).order_by(Contract.created_at.desc())
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = db.scalars(query.offset((page - 1) * limit).limit(limit)).all()

    return ContractListResponse(
        items=[ContractResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        limit=limit,
    )


@router.post("", response_model=ContractResponse, status_code=status.HTTP_201_CREATED)
def create_contract(
    payload: ContractCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ContractResponse:
    contract = Contract(
        contract_number=_generate_contract_number(db),
        title=payload.title,
        contract_type=payload.contract_type,
        vendor_name=payload.vendor_name,
        amount=payload.amount,
        start_date=payload.start_date,
        end_date=payload.end_date,
        metadata_json=payload.metadata,
        file_path=payload.file_path,
        created_by=current_user.id,
        assigned_to=payload.assigned_to,
    )
    db.add(contract)
    db.commit()
    db.refresh(contract)
    return ContractResponse.model_validate(contract)


@router.get("/{contract_id}", response_model=ContractResponse)
def get_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ContractResponse:
    contract = db.scalar(select(Contract).where(Contract.id == contract_id, Contract.status != ContractStatus.deleted))
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")
    return ContractResponse.model_validate(contract)


@router.put("/{contract_id}", response_model=ContractResponse)
def update_contract(
    contract_id: int,
    payload: ContractUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ContractResponse:
    contract = db.scalar(select(Contract).where(Contract.id == contract_id, Contract.status != ContractStatus.deleted))
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")

    updates = payload.model_dump(exclude_none=True)
    if "metadata" in updates:
        updates["metadata_json"] = updates.pop("metadata")

    for key, value in updates.items():
        setattr(contract, key, value)

    db.commit()
    db.refresh(contract)
    return ContractResponse.model_validate(contract)


@router.delete("/{contract_id}", response_model=MessageResponse)
def delete_contract(
    contract_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> MessageResponse:
    contract = db.scalar(select(Contract).where(Contract.id == contract_id, Contract.status != ContractStatus.deleted))
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")

    contract.status = ContractStatus.deleted
    db.commit()
    return MessageResponse(message="Contract soft-deleted")


@router.post("/search", response_model=ContractListResponse)
def search_contracts(
    payload: ContractSearchRequest,
    page: int = 1,
    limit: int = 20,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ContractListResponse:
    query = select(Contract).where(
        and_(
            Contract.status != ContractStatus.deleted,
            or_(
                Contract.title.ilike(f"%{payload.query}%"),
                Contract.vendor_name.ilike(f"%{payload.query}%"),
                Contract.contract_number.ilike(f"%{payload.query}%"),
            ),
        )
    )

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = db.scalars(query.offset((page - 1) * limit).limit(limit)).all()
    return ContractListResponse(
        items=[ContractResponse.model_validate(item) for item in items],
        total=total,
        page=page,
        limit=limit,
    )
