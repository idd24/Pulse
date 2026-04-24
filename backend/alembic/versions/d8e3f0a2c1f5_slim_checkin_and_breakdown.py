"""slim checkin and breakdown

Drops `screen_time_minutes` + `top_category` from `daily_checkins` (moved to
the screentime breakdown table), and trims `screentime_breakdowns` to the
three categories actually surfaced in the UI (social, entertainment,
productivity).

Revision ID: d8e3f0a2c1f5
Revises: c4d7f1e2a9b3
Create Date: 2026-04-24 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d8e3f0a2c1f5"
down_revision: Union[str, Sequence[str], None] = "c4d7f1e2a9b3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # daily_checkins: drop screen_time + top_category
    op.drop_constraint(
        "ck_daily_checkin_screen_time", "daily_checkins", type_="check"
    )
    op.drop_column("daily_checkins", "screen_time_minutes")
    op.drop_column("daily_checkins", "top_category")

    # screentime_breakdowns: drop games/communication/other
    for name in ("games", "communication", "other"):
        op.drop_constraint(
            f"ck_screentime_{name}_range",
            "screentime_breakdowns",
            type_="check",
        )
        op.drop_column("screentime_breakdowns", f"{name}_minutes")


def downgrade() -> None:
    # screentime_breakdowns: re-add the three dropped category columns
    for name in ("games", "communication", "other"):
        op.add_column(
            "screentime_breakdowns",
            sa.Column(
                f"{name}_minutes",
                sa.Integer(),
                nullable=False,
                server_default="0",
            ),
        )
        op.create_check_constraint(
            f"ck_screentime_{name}_range",
            "screentime_breakdowns",
            f"{name}_minutes BETWEEN 0 AND 1440",
        )

    # daily_checkins: re-add screen_time + top_category
    op.add_column(
        "daily_checkins",
        sa.Column(
            "screen_time_minutes",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "daily_checkins",
        sa.Column("top_category", sa.String(length=32), nullable=True),
    )
    op.create_check_constraint(
        "ck_daily_checkin_screen_time",
        "daily_checkins",
        "screen_time_minutes >= 0",
    )
