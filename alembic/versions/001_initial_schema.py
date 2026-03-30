"""Initial schema: Quote and Configuration tables.

Revision ID: 001
Revises:
Create Date: 2026-03-30 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial schema with Quote and Configuration tables."""
    # Create configurations table
    op.create_table(
        "configurations",
        sa.Column("id", sa.UUID(), nullable=False, primary_key=True),
        sa.Column("organization_id", sa.UUID(), nullable=True),
        sa.Column("premium_rate", sa.Numeric(precision=10, scale=6), nullable=False),
        sa.Column("brokerage_rate", sa.Numeric(precision=10, scale=6), nullable=False),
        sa.Column("effective_from", sa.DateTime(), nullable=False),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Index("idx_configurations_organization_id", "organization_id"),
    )

    # Create quotes table
    op.create_table(
        "quotes",
        sa.Column("id", sa.UUID(), nullable=False, primary_key=True),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("loan_value", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("premium_rate", sa.Numeric(precision=10, scale=6), nullable=False),
        sa.Column("premium_amount", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("brokerage_rate", sa.Numeric(precision=10, scale=6), nullable=False),
        sa.Column("brokerage_amount", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("total_amount", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("monthly_payment", sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Index("idx_quotes_organization_id", "organization_id"),
        sa.Index("idx_quotes_user_id", "user_id"),
        sa.Index("idx_quotes_status", "status"),
        sa.Index("idx_quotes_created_at", "created_at"),
    )


def downgrade() -> None:
    """Drop tables."""
    op.drop_table("quotes")
    op.drop_table("configurations")
