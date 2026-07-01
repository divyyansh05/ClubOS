from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy import String, Float, Text, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class MemoryBase(DeclarativeBase):
    pass


class AgentMemoryORM(MemoryBase):
    __tablename__ = "agent_memory"

    memory_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    agent_name: Mapped[str] = mapped_column(String(50), nullable=False)
    memory_type: Mapped[str] = mapped_column(String(50), nullable=False)
    subject_key: Mapped[str] = mapped_column(String(200), nullable=False)
    subject_metadata: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class AgentMemoryRead(BaseModel):
    memory_id: str
    agent_name: str
    memory_type: str
    subject_key: str
    subject_metadata: str | None = None
    occurred_at: datetime
    expires_at: datetime | None = None
    confidence: float | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
