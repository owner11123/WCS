"""Backfill location row/layer/col

Revision ID: ea12277db953
Revises: 888876f8f214
Create Date: 2026-03-22 19:11:04.311421

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ea12277db953'
down_revision: Union[str, Sequence[str], None] = '888876f8f214'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        "UPDATE location "
        "SET row_no = split_part(code, '-', 1)::int, "
        "    layer_no = split_part(code, '-', 2)::int, "
        "    col_no = split_part(code, '-', 3)::int "
        "WHERE code ~ '^[0-9]+-[0-9]+-[0-9]+$' "
        "  AND (row_no IS NULL OR layer_no IS NULL OR col_no IS NULL)"
    )
    op.execute(
        "UPDATE location "
        "SET warehouse_code = split_part(code, '-', 1), "
        "    area_code = split_part(code, '-', 2), "
        "    row_no = split_part(code, '-', 3)::int, "
        "    layer_no = split_part(code, '-', 4)::int, "
        "    col_no = split_part(code, '-', 5)::int "
        "WHERE code ~ '^[^-]+-[^-]+-[0-9]+-[0-9]+-[0-9]+$' "
        "  AND (warehouse_code IS NULL OR area_code IS NULL OR row_no IS NULL OR layer_no IS NULL OR col_no IS NULL)"
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
