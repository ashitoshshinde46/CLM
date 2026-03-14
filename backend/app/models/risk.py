from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    contract_id: Mapped[int] = mapped_column(ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False)
    risk_score: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False)
    high_risk_clauses: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    compliance_status: Mapped[str] = mapped_column(String(50), nullable=False)
    assessed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    assessed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
