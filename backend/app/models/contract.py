from datetime import date, datetime
from enum import Enum
from decimal import Decimal

from sqlalchemy import Date, DateTime, Enum as SQLEnum, ForeignKey, Integer, JSON, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class ContractStatus(str, Enum):
    draft = "draft"
    sent = "sent"
    negotiating = "negotiating"
    signed = "signed"
    active = "active"
    expired = "expired"
    terminated = "terminated"
    deleted = "deleted"


class ContractType(str, Enum):
    vendor = "vendor"
    employee = "employee"
    service = "service"
    lease = "lease"
    nda = "nda"


class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    contract_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[ContractStatus] = mapped_column(
        SQLEnum(ContractStatus, name="contract_status"),
        nullable=False,
        default=ContractStatus.draft,
    )
    contract_type: Mapped[ContractType] = mapped_column(SQLEnum(ContractType, name="contract_type"), nullable=False)
    vendor_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    assigned_to: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    workflows = relationship("Workflow", back_populates="contract", cascade="all, delete-orphan")
    document_versions = relationship("DocumentVersion", back_populates="contract", cascade="all, delete-orphan")
    obligations = relationship("Obligation", back_populates="contract", cascade="all, delete-orphan")
    risk_assessments = relationship("RiskAssessment", cascade="all, delete-orphan")
