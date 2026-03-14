from collections import defaultdict
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user
from app.models.contract import Contract, ContractStatus
from app.models.risk import RiskAssessment
from app.models.user import User
from app.schemas.risk import RiskAssessmentResponse, RiskDashboardItem, RiskDashboardResponse

router = APIRouter(prefix="/risk", tags=["Risk & Compliance"])

HIGH_RISK_KEYWORDS = {
    "unlimited liability": 0.20,
    "auto-renewal": 0.15,
    "indemnity": 0.15,
    "termination for convenience": 0.12,
    "penalty": 0.10,
    "exclusive": 0.08,
}


def _contract_text(contract: Contract) -> str:
    parts: list[str] = [contract.title or "", contract.vendor_name or "", contract.contract_number or ""]
    if contract.metadata_json:
        parts.append(str(contract.metadata_json))
    return " ".join(parts).lower()


def _assess_risk(contract: Contract) -> tuple[Decimal, list[dict], str]:
    text = _contract_text(contract)
    score = 0.05
    findings: list[dict] = []

    for keyword, weight in HIGH_RISK_KEYWORDS.items():
        if keyword in text:
            score += weight
            findings.append({"clause": keyword, "risk_weight": weight})

    if contract.amount and contract.amount >= Decimal("1000000"):
        score += 0.12
        findings.append({"clause": "high contract value", "risk_weight": 0.12})

    if contract.end_date and contract.start_date and (contract.end_date - contract.start_date).days > 365 * 3:
        score += 0.10
        findings.append({"clause": "long contract duration", "risk_weight": 0.10})

    normalized = max(Decimal("0.00"), min(Decimal("1.00"), Decimal(str(round(score, 2)))))
    compliance_status = "review_required" if normalized >= Decimal("0.60") else "compliant"
    return normalized, findings, compliance_status


@router.post("/assess/{contract_id}", response_model=RiskAssessmentResponse, status_code=status.HTTP_201_CREATED)
def assess_contract_risk(
    contract_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RiskAssessmentResponse:
    contract = db.scalar(select(Contract).where(Contract.id == contract_id, Contract.status != ContractStatus.deleted))
    if not contract:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contract not found")

    risk_score, findings, compliance_status = _assess_risk(contract)
    assessment = RiskAssessment(
        contract_id=contract_id,
        risk_score=risk_score,
        high_risk_clauses=findings,
        compliance_status=compliance_status,
        assessed_by=current_user.id,
    )
    db.add(assessment)
    db.commit()
    db.refresh(assessment)
    return RiskAssessmentResponse.model_validate(assessment)


@router.get("/dashboard", response_model=RiskDashboardResponse)
def risk_dashboard(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> RiskDashboardResponse:
    assessments = db.scalars(select(RiskAssessment)).all()
    if not assessments:
        return RiskDashboardResponse(by_vendor=[], by_type=[])

    contract_map = {
        c.id: c
        for c in db.scalars(select(Contract).where(Contract.status != ContractStatus.deleted)).all()
    }

    vendor_groups: dict[str, list[float]] = defaultdict(list)
    type_groups: dict[str, list[float]] = defaultdict(list)

    for a in assessments:
        contract = contract_map.get(a.contract_id)
        if not contract:
            continue
        vendor_key = contract.vendor_name or "unknown"
        type_key = contract.contract_type.value
        score = float(a.risk_score)
        vendor_groups[vendor_key].append(score)
        type_groups[type_key].append(score)

    by_vendor = [
        RiskDashboardItem(
            grouping_key=key,
            total_contracts=len(scores),
            average_risk_score=round(sum(scores) / len(scores), 2),
        )
        for key, scores in sorted(vendor_groups.items())
    ]
    by_type = [
        RiskDashboardItem(
            grouping_key=key,
            total_contracts=len(scores),
            average_risk_score=round(sum(scores) / len(scores), 2),
        )
        for key, scores in sorted(type_groups.items())
    ]

    return RiskDashboardResponse(by_vendor=by_vendor, by_type=by_type)


@router.get("/{contract_id}", response_model=RiskAssessmentResponse)
def contract_risk_report(
    contract_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> RiskAssessmentResponse:
    assessment = db.scalar(
        select(RiskAssessment)
        .where(RiskAssessment.contract_id == contract_id)
        .order_by(RiskAssessment.assessed_at.desc())
    )
    if not assessment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Risk assessment not found")
    return RiskAssessmentResponse.model_validate(assessment)
