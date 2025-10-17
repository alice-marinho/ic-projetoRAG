"""renomear coluna content para message

Revision ID: 7daf9cf68a6d
Revises: b1e2a328701b
Create Date: 2025-10-16 16:49:54.742321

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7daf9cf68a6d'
down_revision: Union[str, Sequence[str], None] = 'b1e2a328701b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
