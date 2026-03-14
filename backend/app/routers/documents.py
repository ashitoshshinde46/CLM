from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user
from app.models.contract import Contract, ContractStatus
from app.models.document import ClauseLibrary, DocumentVersion
from app.models.user import User
from app.schemas.common import MessageResponse
from app.schemas.document import (
    ClauseCreate,
    ClauseGenerateRequest,
    ClauseGenerateResponse,
    ClauseResponse,
    ClauseUpdate,
    DocumentVersionCreate,
    DocumentVersionResponse,
)

router = APIRouter(prefix="/documents", tags=["Document Management"])
clause_router = APIRouter(prefix="/clauses", tags=["Document Management"])


@router.post("/{contract_id}/version", response_model=DocumentVersionResponse, status_code=status.HTTP_201_CREATED)
def upload_version(
    contract_id: int,
    payload: DocumentVersionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DocumentVersionResponse:
    contract = db.scalar(select(Contract).where(Contract.id == contract_id, Contract.status != ContractStatus.deleted))
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")

    current_max = db.scalar(select(func.max(DocumentVersion.version_number)).where(DocumentVersion.contract_id == contract_id))
    next_version = (current_max or 0) + 1

    version = DocumentVersion(
        contract_id=contract_id,
        version_number=next_version,
        file_path=payload.file_path,
        changes_summary=payload.changes_summary,
        created_by=current_user.id,
    )
    db.add(version)
    db.commit()
    db.refresh(version)
    return DocumentVersionResponse.model_validate(version)


@router.get("/{contract_id}/versions", response_model=list[DocumentVersionResponse])
def version_history(
    contract_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[DocumentVersionResponse]:
    contract = db.scalar(select(Contract).where(Contract.id == contract_id, Contract.status != ContractStatus.deleted))
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")

    versions = db.scalars(
        select(DocumentVersion)
        .where(DocumentVersion.contract_id == contract_id)
        .order_by(DocumentVersion.version_number.desc())
    ).all()
    return [DocumentVersionResponse.model_validate(v) for v in versions]


@router.delete("/versions/{version_id}", response_model=MessageResponse)
def delete_version(
    version_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> MessageResponse:
    version = db.scalar(select(DocumentVersion).where(DocumentVersion.id == version_id))
    if not version:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document version not found")

    db.delete(version)
    db.commit()
    return MessageResponse(message="Document version deleted")


@clause_router.post("", response_model=ClauseResponse, status_code=status.HTTP_201_CREATED)
def create_clause(
    payload: ClauseCreate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ClauseResponse:
    clause = ClauseLibrary(
        name=payload.name,
        category=payload.category,
        content=payload.content,
        tags=payload.tags,
    )
    db.add(clause)
    db.commit()
    db.refresh(clause)
    return ClauseResponse.model_validate(clause)


@clause_router.get("", response_model=list[ClauseResponse])
def list_clauses(
    category: str | None = Query(None),
    q: str | None = Query(None),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[ClauseResponse]:
    query = select(ClauseLibrary)
    if category:
        query = query.where(ClauseLibrary.category == category)
    if q:
        query = query.where(ClauseLibrary.name.ilike(f"%{q}%"))

    clauses = db.scalars(query.order_by(ClauseLibrary.usage_count.desc(), ClauseLibrary.id.desc())).all()
    return [ClauseResponse.model_validate(c) for c in clauses]


@clause_router.post("/{clause_id}/use", response_model=MessageResponse)
def increment_clause_usage(
    clause_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> MessageResponse:
    clause = db.scalar(select(ClauseLibrary).where(ClauseLibrary.id == clause_id))
    if not clause:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clause not found")

    clause.usage_count += 1
    db.commit()
    return MessageResponse(message="Clause usage incremented")


@clause_router.put("/{clause_id}", response_model=ClauseResponse)
def update_clause(
    clause_id: int,
    payload: ClauseUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ClauseResponse:
    clause = db.scalar(select(ClauseLibrary).where(ClauseLibrary.id == clause_id))
    if not clause:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clause not found")

    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(clause, key, value)

    db.commit()
    db.refresh(clause)
    return ClauseResponse.model_validate(clause)


@clause_router.delete("/{clause_id}", response_model=MessageResponse)
def delete_clause(
    clause_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> MessageResponse:
    clause = db.scalar(select(ClauseLibrary).where(ClauseLibrary.id == clause_id))
    if not clause:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Clause not found")

    db.delete(clause)
    db.commit()
    return MessageResponse(message="Clause deleted")


@clause_router.post("/generate", response_model=ClauseGenerateResponse)
def generate_document(payload: ClauseGenerateRequest, db: Session = Depends(get_db), _: User = Depends(get_current_user)) -> ClauseGenerateResponse:
    clauses = db.scalars(select(ClauseLibrary).where(ClauseLibrary.id.in_(payload.clause_ids))).all()
    if not clauses and payload.clause_ids:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No matching clauses found")

    ordered = sorted(clauses, key=lambda c: payload.clause_ids.index(c.id)) if payload.clause_ids else []
    clause_text = "\n\n".join(c.content for c in ordered)
    generated = f"{payload.template}\n\n{clause_text}".strip()
    return ClauseGenerateResponse(generated_document=generated)
