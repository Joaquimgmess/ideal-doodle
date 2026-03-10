"""merge heads

Revision ID: c531e17d519d
Revises: 4ec26f37fdb7, ac05b85c4e38, f824054c5b79
Create Date: 2026-03-09 21:23:50.486862

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'c531e17d519d'
down_revision: Union[str, None] = ('4ec26f37fdb7', 'ac05b85c4e38', 'f824054c5b79')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
