"""Backfill location segment codes

Revision ID: 741471c4d5f4
Revises: c5de25bd07b4
Create Date: 2026-03-22 18:23:42.180526

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '741471c4d5f4'
down_revision: Union[str, Sequence[str], None] = 'c5de25bd07b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        "UPDATE location "
        "SET warehouse_code = split_part(code, '-', 1), "
        "    zone_code = split_part(code, '-', 2), "
        "    location_code = split_part(code, '-', 3) "
        "WHERE code ~ '^[^-]+-[^-]+-[^-]+$' "
        "  AND (warehouse_code IS NULL OR zone_code IS NULL OR location_code IS NULL)"
    )
    op.execute(
        "UPDATE location "
        "SET location_code = code "
        "WHERE location_code IS NULL"
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
