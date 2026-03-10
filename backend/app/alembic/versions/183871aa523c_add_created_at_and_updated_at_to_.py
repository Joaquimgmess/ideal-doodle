"""add created_at and updated_at to scraped tables

Revision ID: 183871aa523c
Revises: c531e17d519d
Create Date: 2026-03-09 21:23:58.926594

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '183871aa523c'
down_revision: Union[str, None] = 'c531e17d519d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLES = [
    "evento",
    "feed_item",
    "outro",
    "pedido",
    "pet",
    "ponto_ajuda",
    "voluntario",
]


def upgrade() -> None:
    for table in _TABLES:
        op.add_column(
            table,
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
        )
        op.add_column(
            table,
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.func.now(),
                nullable=False,
            ),
        )


def downgrade() -> None:
    for table in _TABLES:
        op.drop_column(table, "updated_at")
        op.drop_column(table, "created_at")
