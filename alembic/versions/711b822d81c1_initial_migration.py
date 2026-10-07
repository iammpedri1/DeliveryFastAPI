"""Initial Migration

Revision ID: 711b822d81c1
Revises:
Create Date: 2026-10-07 09:39:56.066990
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "711b822d81c1"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "usuarios",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "nome",
            sa.String(100),
            nullable=True,
        ),
        sa.Column(
            "email",
            sa.String(100),
            nullable=False,
        ),
        sa.Column(
            "senha",
            sa.String(100),
            nullable=True,
        ),
        sa.Column(
            "ativo",
            sa.Boolean(),
            nullable=True,
        ),
        sa.Column(
            "admin",
            sa.Boolean(),
            nullable=True,
        ),
    )

    op.create_table(
        "pedidos",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(50),
            nullable=True,
        ),
        sa.Column(
            "usuario",
            sa.Integer(),
            sa.ForeignKey("usuarios.id"),
            nullable=True,
        ),
        sa.Column(
            "preco",
            sa.Float(),
            nullable=True,
        ),
    )

    op.create_table(
        "itens_pedido",
        sa.Column(
            "id",
            sa.Integer(),
            primary_key=True,
            autoincrement=True,
            nullable=False,
        ),
        sa.Column(
            "quantidade",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "sabor",
            sa.String(100),
            nullable=True,
        ),
        sa.Column(
            "tamanho",
            sa.String(50),
            nullable=True,
        ),
        sa.Column(
            "preco_unitario",
            sa.Float(),
            nullable=True,
        ),
        sa.Column(
            "pedido",
            sa.Integer(),
            sa.ForeignKey("pedidos.id"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_table("itens_pedido")
    op.drop_table("pedidos")
    op.drop_table("usuarios")
