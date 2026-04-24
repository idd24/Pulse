from datetime import date, datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import DailyCheckin, DailyCheckinActivity, User
from schemas import DailyCheckinResponse, DailyCheckinUpsert
from security import get_current_user

router = APIRouter(prefix="/api/checkins", tags=["checkins"])


def _resolve_date(x_client_date: Optional[str]) -> date:
    """Trust the client's calendar day (so a 11pm entry doesn't land on tomorrow
    in UTC). Fall back to UTC today if the header is missing or malformed."""
    if x_client_date:
        try:
            return date.fromisoformat(x_client_date)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="X-Client-Date must be YYYY-MM-DD",
            )
    return datetime.now(timezone.utc).date()


def _to_response(checkin: DailyCheckin) -> DailyCheckinResponse:
    return DailyCheckinResponse(
        id=checkin.id,
        date=checkin.date,
        mood=checkin.mood,
        energy=checkin.energy,
        activities=sorted(a.activity for a in checkin.activities),
        updated_at=checkin.updated_at,
    )


@router.get("/today", response_model=Optional[DailyCheckinResponse])
def get_today(
    x_client_date: Optional[str] = Header(default=None, alias="X-Client-Date"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Optional[DailyCheckinResponse]:
    today = _resolve_date(x_client_date)
    checkin = (
        db.query(DailyCheckin)
        .filter(DailyCheckin.user_id == user.id, DailyCheckin.date == today)
        .first()
    )
    return _to_response(checkin) if checkin else None


@router.post(
    "",
    response_model=DailyCheckinResponse,
    status_code=status.HTTP_200_OK,
    summary="Upsert today's check-in",
)
def upsert_today(
    payload: DailyCheckinUpsert,
    x_client_date: Optional[str] = Header(default=None, alias="X-Client-Date"),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> DailyCheckinResponse:
    today = _resolve_date(x_client_date)
    checkin = (
        db.query(DailyCheckin)
        .filter(DailyCheckin.user_id == user.id, DailyCheckin.date == today)
        .first()
    )

    if checkin is None:
        checkin = DailyCheckin(user_id=user.id, date=today)
        db.add(checkin)

    checkin.mood = payload.mood
    checkin.energy = payload.energy

    # Replace the activity set. dedupe in case client sends duplicates.
    checkin.activities = [
        DailyCheckinActivity(activity=a) for a in dict.fromkeys(payload.activities)
    ]

    db.commit()
    db.refresh(checkin)
    return _to_response(checkin)
