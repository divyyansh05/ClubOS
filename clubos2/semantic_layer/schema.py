from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field, field_validator
from sqlalchemy import CheckConstraint, DateTime, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class MetricRegistry(Base):
    __tablename__ = "metric_registry"

    metric_name: Mapped[str] = mapped_column(String(100), primary_key=True)
    business_name: Mapped[str] = mapped_column(String(200), nullable=False)
    definition: Mapped[str] = mapped_column(Text, nullable=False)
    platform: Mapped[str] = mapped_column(String(50), nullable=False)
    polarity: Mapped[str] = mapped_column(
        String(10),
        CheckConstraint("polarity IN ('positive', 'negative')"),
        nullable=False,
    )
    unit: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ambiguous_with: Mapped[str | None] = mapped_column(String(500), nullable=True)
    disambiguation_rule: Mapped[str | None] = mapped_column(Text, nullable=True)
    seasonal_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    typical_range: Mapped[str | None] = mapped_column(String(100), nullable=True)
    valid_query_examples: Mapped[str | None] = mapped_column(Text, nullable=True)
    invalid_query_examples: Mapped[str | None] = mapped_column(Text, nullable=True)
    skill_file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    owned_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    last_reviewed: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )


class MetricRegistryBase(BaseModel):
    metric_name: str = Field(..., max_length=100)
    business_name: str = Field(..., max_length=200)
    definition: str
    platform: str = Field(..., max_length=50)
    polarity: str = Field(..., max_length=10)
    unit: str | None = Field(default=None, max_length=50)
    ambiguous_with: str | None = Field(default=None, max_length=500)
    disambiguation_rule: str | None = None
    seasonal_note: str | None = None
    typical_range: str | None = Field(default=None, max_length=100)
    valid_query_examples: str | None = None
    invalid_query_examples: str | None = None
    skill_file_path: str | None = Field(default=None, max_length=500)
    owned_by: str | None = Field(default=None, max_length=100)
    last_reviewed: datetime | None = None

    @field_validator("polarity")
    @classmethod
    def validate_polarity(cls, v: str) -> str:
        if v not in ("positive", "negative"):
            raise ValueError("polarity must be either 'positive' or 'negative'")
        return v


class MetricRegistryCreate(MetricRegistryBase):
    pass


class MetricRegistryRead(MetricRegistryBase):
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
