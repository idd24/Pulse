from datetime import date, datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy.orm import Session

from database import get_db
from models import ScreentimeBreakdown, User
from schemas import ScreentimeResponse, ScreentimeUpsert
from security import get_current_user

router = APIRouter(prefix="/api/screentime", tags=["screentime"])

DEFAULT_RANGE_DAYS = 30
MAX_RANGE_DAYS = 365


def _resolve_date(x_client_date: Optional[str]) -> date:
    """Trust the client's calendar day so a late-night entry doesn't land on
    tomorrow in UTC. Fall back to UTC today if the header is missing."""
    if x_client_date:
        try:
            return date.fromisoformat(x_client_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="X-Client-Date must be YYYY-MM-DD",
            )
    return datetime.now(timezone.utc).date()


def _to_response(row: ScreentimeBreakdown) -> ScreentimeResponse:
    return ScreentimeResponse(
        id=row.id,
        date=row.date,
        social=row.social_minutes,
        entertainment=row.entertainment_minutes,
        productivity=row.productivity_minutes,
        games=row.games_minutes,
        communication=row.communication_minutes,
        other=row.other_minutes,
        updated_at=row.updated_at,
    )


@router.post(
    "",
    response_model=ScreentimeResponse,
    status_code=status.HTTP_200_OK,
    summary="Upsert today's screen-time breakdown",
)
def upsert_today(
    payload: ScreentimeUpsert,
    x_client_date: Optional[str] = Header(default=None, alias="X-Client-Date"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ScreentimeResponse:
    today = _resolve_date(x_client_date)
    row = (
        db.query(ScreentimeBreakdown)
        .filter(
            ScreentimeBreakdown.user_id == user.id,
            ScreentimeBreakdown.date == today,
        )
        .first()
    )

    if row is None:
        row = ScreentimeBreakdown(user_id=user.id, date=today)
        db.add(row)

    row.social_minutes = payload.social
    row.entertainment_minutes = payload.entertainment
    row.productivity_minutes = payload.productivity
    row.games_minutes = payload.games
    row.communication_minutes = payload.communication
    row.other_minutes = payload.other

    db.commit()
    db.refresh(row)
    return _to_response(row)


@router.get(
    "",
    response_model=list[ScreentimeResponse],
    summary="List screen-time breakdowns over an optional date range",
)
def list_breakdowns(
    start_date: Optional[date] = Query(default=None),
    end_date: Optional[date] = Query(default=None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[ScreentimeResponse]:
    today = datetime.now(timezone.utc).date()
    if start_date is None and end_date is None:
        end_date = today
        start_date = today - timedelta(days=DEFAULT_RANGE_DAYS - 1)
    elif start_date is None:
        start_date = end_date - timedelta(days=MAX_RANGE_DAYS - 1)
    elif end_date is None:
        end_date = min(today, start_date + timedelta(days=MAX_RANGE_DAYS - 1))

    if start_date > end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date must be on or before end_date",
        )
    if (end_date - start_date).days + 1 > MAX_RANGE_DAYS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"date range may not exceed {MAX_RANGE_DAYS} days",
        )

    rows = (
        db.query(ScreentimeBreakdown)
        .filter(
            ScreentimeBreakdown.user_id == user.id,
            ScreentimeBreakdown.date >= start_date,
            ScreentimeBreakdown.date <= end_date,
        )
        .order_by(ScreentimeBreakdown.date.desc())
        .all()
    )
    return [_to_response(r) for r in rows]
