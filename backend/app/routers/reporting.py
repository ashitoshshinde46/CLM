import csv
import io
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import and_, extract, func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import get_current_user
from app.models.contract import Contract, ContractStatus
from app.models.user import User
from app.schemas.reporting import (
    CustomReportItem,
    CustomReportRequest,
    CustomReportResponse,
    SpendAnalyticsResponse,
)

router = APIRouter(prefix="", tags=["Reporting & Analytics"])


def _aging_bucket(contract: Contract) -> str:
    if not contract.end_date:
        return "unknown"
    days_left = (contract.end_date - datetime.utcnow().date()).days
    if days_left < 0:
        return "expired"
    if days_left <= 30:
        return "0-30 days"
    if days_left <= 90:
        return "31-90 days"
    if days_left <= 180:
        return "91-180 days"
    return "181+ days"


@router.get("/reports/contracts-aging")
def contracts_aging(
    format: str = Query("json", pattern="^(json|csv)$"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    contracts = db.scalars(select(Contract).where(Contract.status != ContractStatus.deleted)).all()
    rows = [
        {
            "contract_number": c.contract_number,
            "title": c.title,
            "vendor_name": c.vendor_name,
            "status": c.status.value,
            "start_date": c.start_date.isoformat() if c.start_date else None,
            "end_date": c.end_date.isoformat() if c.end_date else None,
            "aging_bucket": _aging_bucket(c),
        }
        for c in contracts
    ]

    if format == "json":
        return {"items": rows, "total": len(rows)}

    stream = io.StringIO()
    writer = csv.DictWriter(
        stream,
        fieldnames=["contract_number", "title", "vendor_name", "status", "start_date", "end_date", "aging_bucket"],
    )
    writer.writeheader()
    writer.writerows(rows)
    stream.seek(0)
    return StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=contracts_aging.csv"},
    )


@router.get("/analytics/spend", response_model=SpendAnalyticsResponse)
def spend_analytics(
    vendor: str | None = None,
    year: int | None = None,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> SpendAnalyticsResponse:
    query = select(Contract).where(Contract.status != ContractStatus.deleted)
    if vendor:
        query = query.where(Contract.vendor_name == vendor)
    if year:
        query = query.where(extract("year", Contract.start_date) == year)

    contracts = db.scalars(query).all()
    spend_values = [float(c.amount) for c in contracts if c.amount is not None]
    total_contracts = len(contracts)
    total_spend = round(sum(spend_values), 2)
    avg = round((total_spend / len(spend_values)) if spend_values else 0.0, 2)

    return SpendAnalyticsResponse(
        vendor=vendor,
        year=year,
        total_contracts=total_contracts,
        total_spend=total_spend,
        average_contract_value=avg,
    )


@router.post("/reports/custom", response_model=CustomReportResponse)
def custom_report(
    payload: CustomReportRequest,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> CustomReportResponse:
    valid_group = {"status", "vendor", "type"}
    valid_metric = {"count", "sum_amount", "avg_amount"}
    group_by = payload.group_by.lower()
    metric = payload.metric.lower()

    if group_by not in valid_group:
        group_by = "status"
    if metric not in valid_metric:
        metric = "count"

    base_filters = [Contract.status != ContractStatus.deleted]
    if payload.year:
        base_filters.append(extract("year", Contract.start_date) == payload.year)

    if group_by == "status":
        group_expr = Contract.status
    elif group_by == "vendor":
        group_expr = Contract.vendor_name
    else:
        group_expr = Contract.contract_type

    if metric == "count":
        value_expr = func.count(Contract.id)
    elif metric == "sum_amount":
        value_expr = func.coalesce(func.sum(Contract.amount), 0)
    else:
        value_expr = func.coalesce(func.avg(Contract.amount), 0)

    rows = db.execute(
        select(group_expr, value_expr)
        .where(and_(*base_filters))
        .group_by(group_expr)
        .order_by(group_expr)
    ).all()

    items = [CustomReportItem(key=str(row[0] or "unknown"), value=round(float(row[1] or 0), 2)) for row in rows]
    return CustomReportResponse(group_by=group_by, metric=metric, items=items)
