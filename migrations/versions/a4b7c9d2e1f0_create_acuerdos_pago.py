"""create acuerdos_pago

Revision ID: a4b7c9d2e1f0
Revises: fcf3f4ad5370
Create Date: 2026-09-14

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a4b7c9d2e1f0"
down_revision: Union[str, Sequence[str], None] = "fcf3f4ad5370"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "acuerdos_pago",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("empresa_id", sa.Integer(), nullable=False),
        sa.Column("cliente_id", sa.Integer(), nullable=False),
        sa.Column("factura_id", sa.Integer(), nullable=False),
        sa.Column("monto_acordado", sa.Float(), nullable=False),
        sa.Column("numero_cuotas", sa.Integer(), nullable=False),
        sa.Column("valor_cuota", sa.Float(), nullable=False),
        sa.Column("fecha_inicio", sa.DateTime(), nullable=False),
        sa.Column("fecha_fin", sa.DateTime(), nullable=False),
        sa.Column(
            "estado",
            sa.Enum("ACTIVO", "CUMPLIDO", "INCUMPLIDO", "CANCELADO", name="estadoacuerdopago"),
            nullable=False,
        ),
        sa.Column("observaciones", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["empresa_id"], ["empresas.id"]),
        sa.ForeignKeyConstraint(["cliente_id"], ["clientes.id"]),
        sa.ForeignKeyConstraint(["factura_id"], ["facturas.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_acuerdos_pago_empresa_id", "acuerdos_pago", ["empresa_id"]
    )
    op.create_index(
        "ix_acuerdos_pago_factura_id", "acuerdos_pago", ["factura_id"]
    )


def downgrade() -> None:
    op.drop_index("ix_acuerdos_pago_factura_id", table_name="acuerdos_pago")
    op.drop_index("ix_acuerdos_pago_empresa_id", table_name="acuerdos_pago")
    op.drop_table("acuerdos_pago")
