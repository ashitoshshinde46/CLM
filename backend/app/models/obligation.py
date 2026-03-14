from datetime import date, datetime
from enum import Enum

from sqlalchemy import Date, DateTime, Enum as SQLEnum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class ObligationStatus(str, Enum):
    pending = "pending"
    completed = "completed"
    overdue = "overdue"


class Obligation(Base):
    __tablename__ = "obligations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    contract_id: Mapped[int] = mapped_column(ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    responsible_user: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    status: Mapped[ObligationStatus] = mapped_column(
        SQLEnum(ObligationStatus, name="obligation_status"),
        nullable=False,
        default=ObligationStatus.pending,
    )
    recurrence: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    contract = relationship("Contract", back_populates="obligations")
