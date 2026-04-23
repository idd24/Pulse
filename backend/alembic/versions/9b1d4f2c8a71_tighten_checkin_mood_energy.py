"""tighten checkin mood/energy to 0..4

Revision ID: 9b1d4f2c8a71
Revises: 7a2f3c4b1e80
Create Date: 2026-04-23 00:00:01.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "9b1d4f2c8a71"
down_revision: Union[str, Sequence[str], None] = "7a2f3c4b1e80"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Clamp any dev-era rows at 5 so the new CHECK doesn't fail.
    op.execute("UPDATE daily_checkins SET mood = 4 WHERE mood > 4")
    op.execute("UPDATE daily_checkins SET energy = 4 WHERE energy > 4")

    op.drop_constraint("ck_daily_checkin_mood", "daily_checkins", type_="check")
    op.drop_constraint("ck_daily_checkin_energy", "daily_checkins", type_="check")
    op.create_check_constraint(
        "ck_daily_checkin_mood_v2", "daily_checkins", "mood BETWEEN 0 AND 4"
    )
    op.create_check_constraint(
        "ck_daily_checkin_energy_v2", "daily_checkins", "energy BETWEEN 0 AND 4"
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_daily_checkin_mood_v2", "daily_checkins", type_="check"
    )
    op.drop_constraint(
        "ck_daily_checkin_energy_v2", "daily_checkins", type_="check"
    )
    op.create_check_constraint(
        "ck_daily_checkin_mood", "daily_checkins", "mood BETWEEN 0 AND 5"
    )
    op.create_check_constraint(
        "ck_daily_checkin_energy", "daily_checkins", "energy BETWEEN 0 AND 5"
    )
