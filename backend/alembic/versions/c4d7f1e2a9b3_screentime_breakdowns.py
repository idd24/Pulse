"""screentime breakdowns

Revision ID: c4d7f1e2a9b3
Revises: 9b1d4f2c8a71
Create Date: 2026-04-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4d7f1e2a9b3"
down_revision: Union[str, Sequence[str], None] = "9b1d4f2c8a71"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "screentime_breakdowns",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column(
            "social_minutes", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "entertainment_minutes",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "productivity_minutes",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "games_minutes", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column(
            "communication_minutes",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "other_minutes", sa.Integer(), nullable=False, server_default="0"
        ),
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
        sa.CheckConstraint(
            "social_minutes BETWEEN 0 AND 1440",
            name="ck_screentime_social_range",
        ),
        sa.CheckConstraint(
            "entertainment_minutes BETWEEN 0 AND 1440",
            name="ck_screentime_entertainment_range",
        ),
        sa.CheckConstraint(
            "productivity_minutes BETWEEN 0 AND 1440",
            name="ck_screentime_productivity_range",
        ),
        sa.CheckConstraint(
            "games_minutes BETWEEN 0 AND 1440",
            name="ck_screentime_games_range",
        ),
        sa.CheckConstraint(
            "communication_minutes BETWEEN 0 AND 1440",
            name="ck_screentime_communication_range",
        ),
        sa.CheckConstraint(
            "other_minutes BETWEEN 0 AND 1440",
            name="ck_screentime_other_range",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "user_id", "date", name="uq_screentime_user_date"
        ),
    )
    op.create_index(
        op.f("ix_screentime_breakdowns_user_id"),
        "screentime_breakdowns",
        ["user_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        op.f("ix_screentime_breakdowns_user_id"),
        table_name="screentime_breakdowns",
    )
    op.drop_table("screentime_breakdowns")
