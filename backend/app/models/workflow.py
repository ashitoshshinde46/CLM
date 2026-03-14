from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Enum as SQLEnum, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class WorkflowAction(str, Enum):
    approve = "approve"
    reject = "reject"
    comment = "comment"


class Workflow(Base):
    __tablename__ = "workflows"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    contract_id: Mapped[int] = mapped_column(ForeignKey("contracts.id"), nullable=False)
    workflow_type: Mapped[str] = mapped_column(String(100), nullable=False, default="standard")
    current_stage: Mapped[str] = mapped_column(String(50), nullable=False, default="initiated")
    approvers: Mapped[list[dict]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    contract = relationship("Contract", back_populates="workflows")
    events = relationship("WorkflowEvent", back_populates="workflow", cascade="all, delete-orphan")


class WorkflowEvent(Base):
    __tablename__ = "workflow_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    workflow_id: Mapped[int] = mapped_column(ForeignKey("workflows.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    action: Mapped[WorkflowAction] = mapped_column(SQLEnum(WorkflowAction, name="workflow_action"), nullable=False)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    workflow = relationship("Workflow", back_populates="events")
