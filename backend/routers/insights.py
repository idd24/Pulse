from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from insights_pipeline import generate_insights_for_user
from models import Insight, User
from schemas import GenerateInsightsResponse, InsightResponse
from security import get_current_user

router = APIRouter(prefix="/api/insights", tags=["insights"])

# Curated feed cap. Tighter than the raw set so the surface stops feeling
# like a wall of similar cards.
FEED_LIMIT = 6
# How many insights any single category can contribute. With 5 categories
# and 6 slots this leaves room for breadth before any one doubles up.
PER_CATEGORY_CAP = 2


@router.get(
    "",
    response_model=list[InsightResponse],
    summary="List the curated insights feed (ranked, deduped by topic, diversified)",
)
def list_insights(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[InsightResponse]:
    # Pull all rows ranked by effect size, then significance. Persisted set
    # is preserved — we curate at read time so the dedup logic can evolve
    # without re-running the pipeline.
    rows = (
        db.query(Insight)
        .filter(Insight.user_id == user.id)
        .order_by(func.abs(Insight.r).desc(), Insight.p_value.asc())
        .all()
    )
    seen_topics: set[str] = set()
    category_count: dict[str, int] = {}
    feed: list[Insight] = []

    # Pass 1: take the strongest insight from each unseen category. Forces
    # breadth — Mood, Energy, Habits etc. each get a slot before Screen time
    # doubles up.
    for row in rows:
        if len(feed) >= FEED_LIMIT:
            break
        if row.topic in seen_topics:
            continue
        if row.category in category_count:
            continue
        seen_topics.add(row.topic)
        category_count[row.category] = 1
        feed.append(row)

    # Pass 2: fill remaining slots by overall strength, capped per category.
    for row in rows:
        if len(feed) >= FEED_LIMIT:
            break
        if row.topic in seen_topics:
            continue
        if category_count.get(row.category, 0) >= PER_CATEGORY_CAP:
            continue
        seen_topics.add(row.topic)
        category_count[row.category] = category_count.get(row.category, 0) + 1
        feed.append(row)

    # Selection order interleaves categories; sort the final feed by strength
    # so the strongest cards land at the top of the screen.
    feed.sort(key=lambda i: (-abs(i.r), i.p_value))
    return [InsightResponse.model_validate(r) for r in feed]


@router.get(
    "/top",
    response_model=list[InsightResponse],
    summary="Return the current user's strongest insights, ranked by |r|",
)
def list_top_insights(
    limit: int = Query(3, ge=1, le=10),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[InsightResponse]:
    rows = (
        db.query(Insight)
        .filter(Insight.user_id == user.id)
        .order_by(func.abs(Insight.r).desc(), Insight.p_value.asc())
        .limit(limit)
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
