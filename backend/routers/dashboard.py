from datetime import date, datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import case, func
from sqlalchemy.orm import Session

from database import get_db
from models import DailyCheckin, ScreentimeBreakdown, User
from schemas import (
    DashboardSummaryResponse,
    DashboardWeekMetrics,
    TrendsRange,
    TrendsResponse,
)
from security import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])

_RANGE_DAYS: dict[str, int] = {"7d": 7, "30d": 30, "90d": 90}


def _resolve_today(x_client_date: Optional[str]) -> date:
    """Trust the client's calendar day; fall back to UTC today. Mirrors the
    contract used by routers/checkins.py and routers/screentime.py."""
    if x_client_date:
        try:
            return date.fromisoformat(x_client_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="X-Client-Date must be YYYY-MM-DD",
            )
    return datetime.now(timezone.utc).date()


@router.get(
    "/summary",
    response_model=DashboardSummaryResponse,
    summary="Weekly dashboard summary with week-over-week comparison",
)
def get_summary(
    x_client_date: Optional[str] = Header(default=None, alias="X-Client-Date"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DashboardSummaryResponse:
    today = _resolve_today(x_client_date)
    curr_start, curr_end = today - timedelta(days=6), today
    prev_start, prev_end = today - timedelta(days=13), today - timedelta(days=7)

    # Conditional aggregation: one query returns current + previous aggregates.
    # AVG/COUNT over a CASE that resolves to NULL for the wrong week silently
    # skips those rows, so missing days never become zeros in the average.
    is_current = DailyCheckin.date >= curr_start
    checkin_agg = (
        db.query(
            func.avg(case((is_current, DailyCheckin.mood))).label("c_mood"),
            func.avg(case((is_current, DailyCheckin.energy))).label("c_energy"),
            func.count(case((is_current, 1))).label("c_count"),
            func.avg(case((~is_current, DailyCheckin.mood))).label("p_mood"),
            func.avg(case((~is_current, DailyCheckin.energy))).label("p_energy"),
            func.count(case((~is_current, 1))).label("p_count"),
        )
        .filter(
            DailyCheckin.user_id == user.id,
            DailyCheckin.date >= prev_start,
            DailyCheckin.date <= curr_end,
        )
        .one()
    )

    total_min = (
        ScreentimeBreakdown.social_minutes
        + ScreentimeBreakdown.entertainment_minutes
        + ScreentimeBreakdown.productivity_minutes
    )
    is_current_st = ScreentimeBreakdown.date >= curr_start
    screen_agg = (
        db.query(
            func.coalesce(func.sum(case((is_current_st, total_min))), 0).label("c_total"),
            func.coalesce(func.sum(case((~is_current_st, total_min))), 0).label("p_total"),
        )
        .filter(
            ScreentimeBreakdown.user_id == user.id,
            ScreentimeBreakdown.date >= prev_start,
            ScreentimeBreakdown.date <= curr_end,
        )
        .one()
    )

    # AVG of SmallInteger returns Decimal on Postgres; cast to float for Pydantic.
    def _avg(v) -> Optional[float]:
        return float(v) if v is not None else None

    return DashboardSummaryResponse(
        current=DashboardWeekMetrics(
            start_date=curr_start,
            end_date=curr_end,
            avg_mood=_avg(checkin_agg.c_mood),
            avg_energy=_avg(checkin_agg.c_energy),
            checkin_count=int(checkin_agg.c_count or 0),
            total_screen_time_minutes=int(screen_agg.c_total or 0),
        ),
        previous=DashboardWeekMetrics(
            start_date=prev_start,
            end_date=prev_end,
            avg_mood=_avg(checkin_agg.p_mood),
            avg_energy=_avg(checkin_agg.p_energy),
            checkin_count=int(checkin_agg.p_count or 0),
            total_screen_time_minutes=int(screen_agg.p_total or 0),
        ),
    )


@router.get(
    "/trends",
    response_model=TrendsResponse,
    summary="Daily mood / energy / screen-time time series for charts",
)
def get_trends(
    period: TrendsRange = Query(
        ..., alias="range", description="Time window: 7d, 30d, or 90d"
    ),
    x_client_date: Optional[str] = Header(default=None, alias="X-Client-Date"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TrendsResponse:
    today = _resolve_today(x_client_date)
    days = _RANGE_DAYS[period]
    start = today - timedelta(days=days - 1)
    end = today

    checkin_rows = (
        db.query(DailyCheckin.date, DailyCheckin.mood, DailyCheckin.energy)
        .filter(
            DailyCheckin.user_id == user.id,
            DailyCheckin.date >= start,
            DailyCheckin.date <= end,
        )
        .all()
    )
    checkin_by_date = {r.date: r for r in checkin_rows}

    total_min = (
        ScreentimeBreakdown.social_minutes
        + ScreentimeBreakdown.entertainment_minutes
        + ScreentimeBreakdown.productivity_minutes
    )
    screen_rows = (
        db.query(ScreentimeBreakdown.date, total_min.label("total"))
        .filter(
            ScreentimeBreakdown.user_id == user.id,
            ScreentimeBreakdown.date >= start,
            ScreentimeBreakdown.date <= end,
        )
        .all()
    )
    screen_by_date = {r.date: int(r.total) for r in screen_rows}

    # Build the complete ascending date series in Python so gaps surface as
    # null without depending on Postgres-specific generate_series.
    dates: list[date] = [start + timedelta(days=i) for i in range(days)]
    mood: list[Optional[int]] = []
    energy: list[Optional[int]] = []
    screen: list[Optional[int]] = []
    for d in dates:
        c = checkin_by_date.get(d)
        mood.append(int(c.mood) if c else None)
        energy.append(int(c.energy) if c else None)
        screen.append(screen_by_date.get(d))

    return TrendsResponse(
        range=period,
        start_date=start,
        end_date=end,
        dates=dates,
        mood=mood,
        energy=energy,
        screen_time_minutes=screen,
    )
