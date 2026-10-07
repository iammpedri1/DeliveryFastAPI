"""Tabela Pizza

Revision ID: 5812eb72a3df
Revises: 711b822d81c1
Create Date: 2026-10-07 13:54:31.332411

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlalchemy_utils


revision: str = "5812eb72a3df"
down_revision: Union[str, Sequence[str], None] = "711b822d81c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ESCOLHAS_TAMANHO = [("P", "Pequena"), ("M", "Média"), ("G", "Grande")]
ESCOLHAS_STATUS = [
    ("pendente", "Pendente"),
    ("preparando", "Preparando"),
    ("entregue", "Entregue"),
]


def upgrade() -> None:
    """Upgrade schema."""
    with op.batch_alter_table("itens_pedido", schema=None) as batch_op:
        batch_op.alter_column(
            "tamanho",
            existing_type=sa.VARCHAR(length=50),
            type_=sqlalchemy_utils.types.choice.ChoiceType(ESCOLHAS_TAMANHO),
            existing_nullable=True,
        )

    with op.batch_alter_table("pedidos", schema=None) as batch_op:
        batch_op.alter_column(
            "status",
            existing_type=sa.VARCHAR(length=50),
            type_=sqlalchemy_utils.types.choice.ChoiceType(ESCOLHAS_STATUS),
            existing_nullable=True,
        )


def downgrade() -> None:
    """Downgrade schema."""

    with op.batch_alter_table("pedidos", schema=None) as batch_op:
        batch_op.alter_column(
            "status",
            existing_type=sqlalchemy_utils.types.choice.ChoiceType(ESCOLHAS_STATUS),
            type_=sa.VARCHAR(length=50),
            existing_nullable=True,
        )

    with op.batch_alter_table("itens_pedido", schema=None) as batch_op:
        batch_op.alter_column(
            "tamanho",
            existing_type=sqlalchemy_utils.types.choice.ChoiceType(ESCOLHAS_TAMANHO),
            type_=sa.VARCHAR(length=50),
            existing_nullable=True,
        )
