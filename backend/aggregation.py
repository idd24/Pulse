"""Build a wide, one-row-per-day pandas DataFrame for a single user.

Joins `daily_checkins` (mood, energy, activities) with `screentime_breakdowns`
(per-category minutes) into a frame ready to feed into a future correlation
engine. Outer join on date so days with only one signal aren't dropped.
"""

from typing import get_args
from uuid import UUID

import pandas as pd
from sqlalchemy.orm import Session, selectinload

from models import DailyCheckin, ScreentimeBreakdown
from schemas import Activity

# Single source of truth for the activity set — stays in sync with the API schema.
ACTIVITIES: tuple[str, ...] = get_args(Activity)
_ACTIVITY_COLS: list[str] = [f"did_{a}" for a in ACTIVITIES]

_FINAL_COLUMNS: list[str] = [
    "date",
    "day_of_week",
    "is_weekend",
    "mood",
    "energy",
    "social_screen_time",
    "entertainment_screen_time",
    "productivity_screen_time",
    "total_screen_time",
    *_ACTIVITY_COLS,
]


def build_daily_dataframe(user_id: UUID, db: Session) -> pd.DataFrame:
    """Return one user's full history as a daily DataFrame.

    One row per date that has either a check-in or a screen-time entry. Missing
    fields are pandas `NA` (mood/energy stay nullable Int8; screen-time stays
    nullable Int32; activity flags stay nullable boolean). Sorted by date asc.
    """
    checkins = (
        db.query(DailyCheckin)
        .options(selectinload(DailyCheckin.activities))
        .filter(DailyCheckin.user_id == user_id)
        .all()
    )
    breakdowns = (
        db.query(ScreentimeBreakdown)
        .filter(ScreentimeBreakdown.user_id == user_id)
        .all()
    )

    checkin_records = []
    for c in checkins:
        done = {a.activity for a in c.activities}
        row = {
            "date": c.date,
            "mood": c.mood,
            "energy": c.energy,
            **{f"did_{name}": (name in done) for name in ACTIVITIES},
        }
        checkin_records.append(row)

    checkin_df = pd.DataFrame.from_records(
        checkin_records,
        columns=["date", "mood", "energy", *_ACTIVITY_COLS],
    )

    screen_df = pd.DataFrame.from_records(
        [
            {
                "date": s.date,
                "social_screen_time": s.social_minutes,
                "entertainment_screen_time": s.entertainment_minutes,
                "productivity_screen_time": s.productivity_minutes,
            }
            for s in breakdowns
        ],
        columns=[
            "date",
            "social_screen_time",
            "entertainment_screen_time",
            "productivity_screen_time",
        ],
    )

    df = pd.merge(checkin_df, screen_df, on="date", how="outer")

    # Nullable extension dtypes preserve NA across the outer join — plain int/bool would
    # silently coerce missing rows to 0/False and lose the "not logged" signal.
    df["date"] = pd.to_datetime(df["date"])
    df["mood"] = df["mood"].astype("Int8")
    df["energy"] = df["energy"].astype("Int8")
    for col in (
        "social_screen_time",
        "entertainment_screen_time",
        "productivity_screen_time",
    ):
        df[col] = df[col].astype("Int32")
    for col in _ACTIVITY_COLS:
        df[col] = df[col].astype("boolean")

    df["total_screen_time"] = (
        df["social_screen_time"]
        + df["entertainment_screen_time"]
        + df["productivity_screen_time"]
    ).astype("Int32")

    df["day_of_week"] = df["date"].dt.day_name().astype("string")
    df["is_weekend"] = df["date"].dt.dayofweek >= 5

    df = df.sort_values("date", ignore_index=True)
    return df[_FINAL_COLUMNS]
