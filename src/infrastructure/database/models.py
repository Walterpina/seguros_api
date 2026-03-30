"""SQLAlchemy ORM models for Quote and Configuration."""

from datetime import datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    DECIMAL,
    DateTime,
    Index,
    String,
    UUID as SQLAUUID,
    func,
)
from sqlalchemy.orm import declarative_base, Mapped, mapped_column

Base = declarative_base()


class Configuration(Base):
    """Configuration entity: Premium and brokerage rates by organization."""

    __tablename__ = "configurations"

    id: Mapped[UUID] = mapped_column(
        SQLAUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
    )
    organization_id: Mapped[Optional[UUID]] = mapped_column(
        SQLAUUID(as_uuid=True),
        nullable=True,
        index=True,
    )
    premium_rate: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=10, scale=6),
        nullable=False,
        comment="Premium rate as decimal (e.g., 0.045 = 4.5%)",
    )
    brokerage_rate: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=10, scale=6),
        nullable=False,
        comment="Brokerage rate as decimal (e.g., 0.15 = 15%)",
    )
    effective_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        comment="Date when this configuration becomes active",
    )
    created_by: Mapped[Optional[UUID]] = mapped_column(
        SQLAUUID(as_uuid=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        default=datetime.utcnow,
    )

    __table_args__ = (
        Index("idx_configurations_organization_id", "organization_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<Configuration(id={self.id}, organization_id={self.organization_id}, "
            f"premium_rate={self.premium_rate}, brokerage_rate={self.brokerage_rate})>"
        )


class Quote(Base):
    """Quote entity: Lending insurance quotation with calculated amounts."""

    __tablename__ = "quotes"

    id: Mapped[UUID] = mapped_column(
        SQLAUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        nullable=False,
    )
    organization_id: Mapped[UUID] = mapped_column(
        SQLAUUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        SQLAUUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    loan_value: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=15, scale=2),
        nullable=False,
        comment="Principal loan amount (e.g., 100000.00)",
    )
    premium_rate: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=10, scale=6),
        nullable=False,
        comment="Premium rate used in calculation",
    )
    premium_amount: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=15, scale=2),
        nullable=False,
        comment="Calculated premium (loan_value * premium_rate)",
    )
    brokerage_rate: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=10, scale=6),
        nullable=False,
        comment="Brokerage rate used in calculation",
    )
    brokerage_amount: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=15, scale=2),
        nullable=False,
        comment="Calculated brokerage (premium_amount * brokerage_rate)",
    )
    total_amount: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=15, scale=2),
        nullable=False,
        comment="Total (loan_value + premium_amount + brokerage_amount)",
    )
    monthly_payment: Mapped[Decimal] = mapped_column(
        DECIMAL(precision=15, scale=2),
        nullable=False,
        comment="Monthly payment amount for the quotation",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="active",
        comment="Status: active, archived, cancelled",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        default=datetime.utcnow,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=False),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    __table_args__ = (
        Index("idx_quotes_organization_id", "organization_id"),
        Index("idx_quotes_user_id", "user_id"),
        Index("idx_quotes_status", "status"),
        Index("idx_quotes_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<Quote(id={self.id}, organization_id={self.organization_id}, "
            f"user_id={self.user_id}, loan_value={self.loan_value}, "
            f"total_amount={self.total_amount}, status={self.status})>"
        )
