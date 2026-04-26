"""insights table

Stores generated correlation insights, one row per
(user, template_key, variable_a, variable_b). Pipeline upserts on this key.

Revision ID: f3a8c1e9b2d6
Revises: d8e3f0a2c1f5
Create Date: 2026-04-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f3a8c1e9b2d6"
down_revision: Union[str, Sequence[str], None] = "d8e3f0a2c1f5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "insights",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("template_key", sa.String(length=64), nullable=False),
        sa.Column("variable_a", sa.String(length=64), nullable=False),
        sa.Column("variable_b", sa.String(length=64), nullable=False),
        sa.Column("direction", sa.String(length=16), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("r", sa.Float(), nullable=False),
        sa.Column("p_value", sa.Float(), nullable=False),
        sa.Column("n", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id",
            "template_key",
            "variable_a",
            "variable_b",
            name="uq_insight_user_template_pair",
        ),
    )
    op.create_index(
        op.f("ix_insights_user_id"),
        "insights",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_insights_user_id"), table_name="insights")
    op.drop_table("insights")
