from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from database import get_db
from insights_pipeline import generate_insights_for_user
from models import Insight, User
from schemas import GenerateInsightsResponse, InsightResponse
from security import get_current_user

router = APIRouter(prefix="/api/insights", tags=["insights"])


@router.get(
    "",
    response_model=list[InsightResponse],
    summary="List the current user's insights, newest first",
)
def list_insights(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[InsightResponse]:
    rows = (
        db.query(Insight)
        .filter(Insight.user_id == user.id)
        .order_by(Insight.created_at.desc())
        .all()
    )
    return [InsightResponse.model_validate(r) for r in rows]


@router.post(
    "/generate",
    response_model=GenerateInsightsResponse,
    status_code=status.HTTP_200_OK,
    summary="Run the full insights pipeline for the current user",
)
def generate_insights(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> GenerateInsightsResponse:
    result = generate_insights_for_user(user.id, db)
    return GenerateInsightsResponse(
        checkin_count=result.checkin_count,
        skipped_reason=result.skipped_reason,
        pairs_significant=result.pairs_significant,
        pairs_uncovered=result.pairs_uncovered,
        new_count=result.new_count,
        updated_count=result.updated_count,
        insights=[InsightResponse.model_validate(i) for i in result.insights],
    )
