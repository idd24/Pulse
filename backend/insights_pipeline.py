"""End-to-end insights pipeline.

Runs aggregation → correlation → template selection → render → upsert into
the `insights` table for one user. Built to be triggered by the
`/api/insights/generate` dev endpoint or, eventually, a scheduled job.

Upsert key is (user_id, template_key, variable_a, variable_b) so re-running
keeps insights fresh as more data arrives instead of stacking duplicates.
Insights whose underlying correlation no longer reaches significance are
left in place — the row stops being refreshed but isn't deleted.
"""

from dataclasses import dataclass
from typing import Optional
from uuid import UUID

from sqlalchemy.orm import Session

from aggregation import build_daily_dataframe
from correlation import analyze_correlations
from insight_templates import (
    ACTIVITY_LABELS,
    INSIGHT_TEMPLATES,
    OUTCOME_LABELS,
    SCREENTIME_LABELS,
    InsightTemplate,
    confidence_from_p,
)
from models import DailyCheckin, Insight

MIN_CHECKINS = 14

_TEMPLATES_BY_KEY: dict[str, InsightTemplate] = {t.key: t for t in INSIGHT_TEMPLATES}


# --- Variable-pair → template selection -----------------------------------

def _classify(var: str) -> str:
    if var in OUTCOME_LABELS:
        return "outcome"
    if var in SCREENTIME_LABELS:
        return "screentime"
    if var in ACTIVITY_LABELS:
        return "activity"
    if var == "is_weekend":
        return "weekend"
    return "unknown"


def _pick_template_key(a: str, b: str) -> Optional[str]:
    """Pick the most specific template for a pair, or None if uncovered.
    is_weekend × activity intentionally returns None — no template fits."""
    types = frozenset((_classify(a), _classify(b)))
    if types == {"outcome"}:
        return "mood_energy_couple"
    if "weekend" in types:
        if "outcome" in types or "screentime" in types:
            return "weekend_shift"
        return None
    if types == {"activity", "outcome"}:
        return "activity_affects_outcome"
    if types == {"screentime", "outcome"}:
        return "screentime_affects_outcome"
    if types == {"activity"}:
        return "habits_pair"
    if types == {"screentime"}:
        return "screentime_categories_link"
    if types == {"activity", "screentime"}:
        return "activity_shifts_screentime"
    return None


# --- Placeholder rendering -------------------------------------------------

def _render(
    template: InsightTemplate,
    variable_a: str,
    variable_b: str,
    direction: str,
    n: int,
    p_value: float,
) -> tuple[str, str]:
    """Fill the template placeholders for this pair → (title, body)."""
    conf = confidence_from_p(p_value)
    base = {
        "n": n,
        "confidence_long": conf.long_label,
        "confidence_stars": conf.stars,
    }

    key = template.key
    if key == "mood_energy_couple":
        values = base
    elif key == "activity_affects_outcome":
        act = variable_a if variable_a in ACTIVITY_LABELS else variable_b
        out = variable_b if act == variable_a else variable_a
        al = ACTIVITY_LABELS[act]
        values = {
            **base,
            "activity_title": al["title"],
            "activity_verb_past": al["verb_past"],
            "outcome": OUTCOME_LABELS[out],
        }
    elif key == "screentime_affects_outcome":
        scr = variable_a if variable_a in SCREENTIME_LABELS else variable_b
        out = variable_b if scr == variable_a else variable_a
        sl = SCREENTIME_LABELS[scr]
        values = {
            **base,
            "screen_title": sl["title"],
            "screen_noun": sl["noun"],
            "outcome": OUTCOME_LABELS[out],
        }
    elif key == "habits_pair":
        al = ACTIVITY_LABELS[variable_a]
        bl = ACTIVITY_LABELS[variable_b]
        values = {
            **base,
            "activity_a_title": al["title"],
            "activity_a_verb_past": al["verb_past"],
            "activity_b_noun": bl["noun"],
            "activity_b_verb_past": bl["verb_past"],
        }
    elif key == "weekend_shift":
        other = variable_a if variable_a != "is_weekend" else variable_b
        if other in OUTCOME_LABELS:
            other_noun = OUTCOME_LABELS[other]
        else:
            other_noun = SCREENTIME_LABELS[other]["noun"]
        values = {**base, "other_noun": other_noun, "other_lower": other_noun}
    elif key == "screentime_categories_link":
        al = SCREENTIME_LABELS[variable_a]
        bl = SCREENTIME_LABELS[variable_b]
        values = {
            **base,
            "screen_a_title": al["title"],
            "screen_a_noun": al["noun"],
            "screen_b_noun": bl["noun"],
        }
    elif key == "activity_shifts_screentime":
        act = variable_a if variable_a in ACTIVITY_LABELS else variable_b
        scr = variable_b if act == variable_a else variable_a
        al = ACTIVITY_LABELS[act]
        sl = SCREENTIME_LABELS[scr]
        values = {
            **base,
            "activity_title": al["title"],
            "activity_verb_past": al["verb_past"],
            "screen_noun": sl["noun"],
        }
    else:
        raise ValueError(f"Unknown template key: {key}")

    if direction == "positive":
        return (
            template.title_positive.format(**values),
            template.body_positive.format(**values),
        )
    return (
        template.title_negative.format(**values),
        template.body_negative.format(**values),
    )


# --- Pipeline entrypoint ---------------------------------------------------

@dataclass
class PipelineResult:
    checkin_count: int
    skipped_reason: Optional[str]   # populated when the user is gated out
    pairs_significant: int           # rows from analyze_correlations
    pairs_uncovered: int             # significant pairs no template handled
    new_count: int                   # rows inserted this run
    updated_count: int               # rows refreshed this run
    insights: list[Insight]          # rows touched this run (new + updated)


def generate_insights_for_user(user_id: UUID, db: Session) -> PipelineResult:
    """Aggregate → correlate → render → upsert. Commits at the end."""
    checkin_count = (
        db.query(DailyCheckin).filter(DailyCheckin.user_id == user_id).count()
    )
    if checkin_count < MIN_CHECKINS:
        return PipelineResult(
            checkin_count=checkin_count,
            skipped_reason=f"need_at_least_{MIN_CHECKINS}_checkins",
            pairs_significant=0,
            pairs_uncovered=0,
            new_count=0,
            updated_count=0,
            insights=[],
        )

    df = build_daily_dataframe(user_id, db)
    correlations = analyze_correlations(df)

    if correlations.empty:
        return PipelineResult(
            checkin_count=checkin_count,
            skipped_reason=None,
            pairs_significant=0,
            pairs_uncovered=0,
            new_count=0,
            updated_count=0,
            insights=[],
        )

    new_count = 0
    updated_count = 0
    uncovered = 0
    touched: list[Insight] = []

    for row in correlations.itertuples(index=False):
        template_key = _pick_template_key(row.variable_a, row.variable_b)
        if template_key is None:
            uncovered += 1
            continue

        template = _TEMPLATES_BY_KEY[template_key]
        title, body = _render(
            template,
            row.variable_a,
            row.variable_b,
            row.direction,
            int(row.n),
            float(row.p_value),
        )

        existing = (
            db.query(Insight)
            .filter(
                Insight.user_id == user_id,
                Insight.template_key == template_key,
                Insight.variable_a == row.variable_a,
                Insight.variable_b == row.variable_b,
            )
            .one_or_none()
        )
        if existing is None:
            insight = Insight(
                user_id=user_id,
                template_key=template_key,
                variable_a=row.variable_a,
                variable_b=row.variable_b,
                direction=row.direction,
                title=title,
                body=body,
                r=float(row.r),
                p_value=float(row.p_value),
                n=int(row.n),
            )
            db.add(insight)
            touched.append(insight)
            new_count += 1
        else:
            existing.direction = row.direction
            existing.title = title
            existing.body = body
            existing.r = float(row.r)
            existing.p_value = float(row.p_value)
            existing.n = int(row.n)
            touched.append(existing)
            updated_count += 1

    db.commit()
    for insight in touched:
        db.refresh(insight)

    return PipelineResult(
        checkin_count=checkin_count,
        skipped_reason=None,
        pairs_significant=int(len(correlations)),
        pairs_uncovered=uncovered,
        new_count=new_count,
        updated_count=updated_count,
        insights=touched,
    )
