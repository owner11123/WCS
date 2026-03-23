"""Backfill transit total_quantity

Revision ID: 0cf14b39c2c2
Revises: 1a7e61123e0d
Create Date: 2026-03-22 17:14:05.726174

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0cf14b39c2c2'
down_revision: Union[str, Sequence[str], None] = '1a7e61123e0d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute(
        "UPDATE transit_inventory "
        "SET total_quantity = quantity + received_quantity "
        "WHERE total_quantity = 0 AND (quantity > 0 OR received_quantity > 0)"
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
