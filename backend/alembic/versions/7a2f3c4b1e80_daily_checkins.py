"""daily checkins

Revision ID: 7a2f3c4b1e80
Revises: 5dbaef71d52d
Create Date: 2026-04-23 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7a2f3c4b1e80"
down_revision: Union[str, Sequence[str], None] = "5dbaef71d52d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "daily_checkins",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("mood", sa.SmallInteger(), nullable=False),
        sa.Column("energy", sa.SmallInteger(), nullable=False),
        sa.Column("screen_time_minutes", sa.Integer(), nullable=False),
        sa.Column("top_category", sa.String(length=32), nullable=True),
        sa.Column("note", sa.Text(), nullable=True),
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
        sa.CheckConstraint("mood BETWEEN 0 AND 5", name="ck_daily_checkin_mood"),
        sa.CheckConstraint("energy BETWEEN 0 AND 5", name="ck_daily_checkin_energy"),
        sa.CheckConstraint(
            "screen_time_minutes >= 0", name="ck_daily_checkin_screen_time"
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "date", name="uq_daily_checkin_user_date"),
    )
    op.create_index(
        op.f("ix_daily_checkins_user_id"),
        "daily_checkins",
        ["user_id"],
        unique=False,
    )

    op.create_table(
        "daily_checkin_activities",
        sa.Column("checkin_id", sa.UUID(), nullable=False),
        sa.Column("activity", sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(
            ["checkin_id"], ["daily_checkins.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("checkin_id", "activity"),
    )


def downgrade() -> None:
    op.drop_table("daily_checkin_activities")
    op.drop_index(
        op.f("ix_daily_checkins_user_id"), table_name="daily_checkins"
    )
    op.drop_table("daily_checkins")
