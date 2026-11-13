"""add order delivery tracking

Revision ID: a6c1d98e42b7
Revises: f81bc132a0a6
Create Date: 2026-11-13

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a6c1d98e42b7"
down_revision: Union[str, Sequence[str], None] = "f81bc132a0a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "orders",
        sa.Column("delivery_latitude", sa.Numeric(10, 7), nullable=True),
    )
    op.add_column(
        "orders",
        sa.Column("delivery_longitude", sa.Numeric(10, 7), nullable=True),
    )
    op.add_column(
        "orders",
        sa.Column("rider_latitude", sa.Numeric(10, 7), nullable=True),
    )
    op.add_column(
        "orders",
        sa.Column("rider_longitude", sa.Numeric(10, 7), nullable=True),
    )
    op.add_column(
        "orders",
        sa.Column("location_updated_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "orders",
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("orders", "delivered_at")
    op.drop_column("orders", "location_updated_at")
    op.drop_column("orders", "rider_longitude")
    op.drop_column("orders", "rider_latitude")
    op.drop_column("orders", "delivery_longitude")
    op.drop_column("orders", "delivery_latitude")