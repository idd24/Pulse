"""insight topic and category columns

Adds `topic` (machine ID for dedup) and `category` (user-facing pill label)
to the insights table. Backfills existing rows from template_key + variables
so the columns can be marked NOT NULL.

Revision ID: a1c4e9b6f3d8
Revises: f3a8c1e9b2d6
Create Date: 2026-04-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1c4e9b6f3d8"
down_revision: Union[str, Sequence[str], None] = "f3a8c1e9b2d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Kept inline so the migration is self-contained — mirrors the runtime
# helper in insight_templates.categorize_insight.
_OUTCOMES = {"mood", "energy"}
_SCREENTIME = {
    "social_screen_time",
    "entertainment_screen_time",
    "productivity_screen_time",
    "total_screen_time",
}


def _compute(template_key: str, a: str, b: str) -> tuple[str, str]:
    if template_key == "mood_energy_couple":
        return "mood_energy", "Mood × Energy"
    if template_key in ("activity_affects_outcome", "screentime_affects_outcome"):
        outcome = a if a in _OUTCOMES else b
        return outcome, "Mood" if outcome == "mood" else "Energy"
    if template_key == "weekend_shift":
        other = b if a == "is_weekend" else a
        if other in _OUTCOMES:
            return other, "Mood" if other == "mood" else "Energy"
        return other, "Screen time"
    if template_key == "habits_pair":
        x, y = sorted((a, b))
        return f"habits:{x}:{y}", "Habits"
    if template_key == "screentime_categories_link":
        x, y = sorted((a, b))
        return f"screen_pair:{x}:{y}", "Screen time"
    if template_key == "activity_shifts_screentime":
        screen = a if a in _SCREENTIME else b
        return screen, "Screen time"
    # Fallback for unknown rows — keeps the migration safe.
    return template_key, "Insight"


def upgrade() -> None:
    op.add_column(
        "insights",
        sa.Column("topic", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "insights",
        sa.Column("category", sa.String(length=32), nullable=True),
    )

    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            "SELECT id, template_key, variable_a, variable_b FROM insights"
        )
    ).fetchall()
    for row in rows:
        topic, category = _compute(row.template_key, row.variable_a, row.variable_b)
        conn.execute(
            sa.text(
                "UPDATE insights SET topic = :topic, category = :category "
                "WHERE id = :id"
            ),
            {"topic": topic, "category": category, "id": row.id},
        )

    op.alter_column("insights", "topic", nullable=False)
    op.alter_column("insights", "category", nullable=False)


def downgrade() -> None:
    op.drop_column("insights", "category")
    op.drop_column("insights", "topic")
