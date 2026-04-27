"""End-to-end insights pipeline.

Runs aggregation → correlation → template selection → render → upsert into
the `insights` table for one user. Built to be triggered by the
`/api/insights/generate` dev endpoint or, eventually, a scheduled job.

Upsert key is (user_id, template_key, variable_a, variable_b) so re-running
keeps insights fresh as more data arrives instead of stacking duplicates.
Insights whose underlying correlation no longer reaches significance are
left in place — the row stops being refreshed but isn't deleted.
"""

import math
from dataclasses import dataclass
from typing import Optional
from uuid import UUID

import pandas as pd
from sqlalchemy.orm import Session

from aggregation import build_daily_dataframe
from correlation import analyze_correlations
from insight_templates import (
    ACTIVITY_LABELS,
    INSIGHT_TEMPLATES,
    OUTCOME_LABELS,
    SCREENTIME_LABELS,
    InsightTemplate,
    categorize_insight,
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


# --- Per-template metric helpers ------------------------------------------
# Compute the one number each template surfaces. All return nan on degenerate
# input (empty group, missing variance) so the renderer can fall back to a
# number-free body instead of printing "nan".

def _binary_continuous_means(
    df: pd.DataFrame, binary_var: str, continuous_var: str
) -> tuple[float, float]:
    """Mean of `continuous_var` when `binary_var` is True / False."""
    sub = df[[binary_var, continuous_var]].dropna()
    if sub.empty:
        return float("nan"), float("nan")
    flag = sub[binary_var].astype(bool)
    yes = pd.to_numeric(sub.loc[flag, continuous_var], errors="coerce")
    no = pd.to_numeric(sub.loc[~flag, continuous_var], errors="coerce")
    m_yes = float(yes.mean()) if not yes.empty else float("nan")
    m_no = float(no.mean()) if not no.empty else float("nan")
    return m_yes, m_no


def _continuous_continuous_split(
    df: pd.DataFrame, split_var: str, value_var: str
) -> tuple[float, float]:
    """Median-split on `split_var` → (mean of value above median, mean below-or-equal)."""
    sub = df[[split_var, value_var]].dropna()
    if sub.empty:
        return float("nan"), float("nan")
    split = pd.to_numeric(sub[split_var], errors="coerce")
    value = pd.to_numeric(sub[value_var], errors="coerce")
    med = split.median()
    high = value[split > med]
    low = value[split <= med]
    m_high = float(high.mean()) if not high.empty else float("nan")
    m_low = float(low.mean()) if not low.empty else float("nan")
    return m_high, m_low


def _binary_binary_cooccurrence(
    df: pd.DataFrame, var_a: str, var_b: str
) -> float:
    """P(b=True | a=True), as a 0–100 percentage."""
    sub = df[[var_a, var_b]].dropna()
    a_days = sub[sub[var_a].astype(bool)]
    if a_days.empty:
        return float("nan")
    return float(a_days[var_b].astype(bool).mean()) * 100.0


def _same_side_of_median_pct(
    df: pd.DataFrame, var_a: str, var_b: str
) -> float:
    """% of rows where both vars sit on the same side of their respective medians."""
    sub = df[[var_a, var_b]].dropna()
    if sub.empty:
        return float("nan")
    a = pd.to_numeric(sub[var_a], errors="coerce")
    b = pd.to_numeric(sub[var_b], errors="coerce")
    med_a, med_b = a.median(), b.median()
    same = (a > med_a) == (b > med_b)
    return float(same.mean()) * 100.0


def _finite(*vals: float) -> bool:
    return all(isinstance(v, float) and math.isfinite(v) for v in vals)


# --- Placeholder rendering -------------------------------------------------

def _render(
    template: InsightTemplate,
    variable_a: str,
    variable_b: str,
    direction: str,
    df: pd.DataFrame,
) -> tuple[str, str]:
    """Fill the template placeholders for this pair → (title, body).

    The metric (group means / co-occurrence rate / agreement %) is computed
    from `df` here so the template never has to know about pandas. If the
    metric is nan (degenerate input), falls back to a number-free body.
    """
    key = template.key

    if key == "mood_energy_couple":
        pct = _same_side_of_median_pct(df, "mood", "energy")
        if not _finite(pct):
            return _fallback_mood_energy(template, direction)
        if direction == "negative":
            pct = 100.0 - pct
        # Avoid "0% of days" / "100% of days" — read as flat sentences instead.
        title = (
            template.title_positive if direction == "positive"
            else template.title_negative
        )
        if pct >= 99.5:
            body = (
                "Mood and energy moved in lockstep on every logged day."
                if direction == "positive"
                else "Mood and energy landed on opposite sides of average every day."
            )
            return title, body
        if pct < 1:
            body = (
                "Mood and energy rarely lined up on the same side of average."
                if direction == "positive"
                else "Mood and energy almost always landed on the same side of average."
            )
            return title, body
        return _format_pair(template, direction, {"pct": pct})

    if key == "activity_affects_outcome":
        act = variable_a if variable_a in ACTIVITY_LABELS else variable_b
        out = variable_b if act == variable_a else variable_a
        al, ol = ACTIVITY_LABELS[act], OUTCOME_LABELS[out]
        m_yes, m_no = _binary_continuous_means(df, act, out)
        if not _finite(m_yes, m_no):
            return _fallback_activity_outcome(template, direction, al, ol)
        return _format_pair(template, direction, {
            "activity_title": al["title"],
            "activity_verb_past": al["verb_past"],
            "outcome_title": ol["title"],
            "outcome_lower": ol["noun"],
            "m_yes": m_yes,
            "m_no": m_no,
        })

    if key == "screentime_affects_outcome":
        scr = variable_a if variable_a in SCREENTIME_LABELS else variable_b
        out = variable_b if scr == variable_a else variable_a
        sl, ol = SCREENTIME_LABELS[scr], OUTCOME_LABELS[out]
        m_high, m_low = _continuous_continuous_split(df, scr, out)
        if not _finite(m_high, m_low):
            return _fallback_screentime_outcome(template, direction, sl, ol)
        return _format_pair(template, direction, {
            "screen_title": sl["title"],
            "screen_noun": sl["noun"],
            "outcome_title": ol["title"],
            "outcome_lower": ol["noun"],
            "m_high": m_high,
            "m_low": m_low,
        })

    if key == "habits_pair":
        al = ACTIVITY_LABELS[variable_a]
        bl = ACTIVITY_LABELS[variable_b]
        pct = _binary_binary_cooccurrence(df, variable_a, variable_b)
        if not _finite(pct):
            return _fallback_habits_pair(template, direction, al, bl)
        # 0% / 100% read awkwardly substituted into "Just 0% of days...".
        # Swap to a plain-English sentence at the edges.
        title = (
            template.title_positive if direction == "positive"
            else template.title_negative
        ).format(activity_a_title=al["title"], activity_b_noun=bl["noun"])
        if direction == "negative" and pct < 1:
            return title, (
                f"You haven't {bl['verb_past']} on any of the days you "
                f"{al['verb_past']} so far."
            )
        if direction == "positive" and pct >= 99.5:
            return title, (
                f"Every day you {al['verb_past']}, you also {bl['verb_past']}."
            )
        return _format_pair(template, direction, {
            "activity_a_title": al["title"],
            "activity_a_verb_past": al["verb_past"],
            "activity_b_noun": bl["noun"],
            "activity_b_verb_past": bl["verb_past"],
            "pct": pct,
        })

    if key == "weekend_shift":
        return _render_weekend_shift(template, variable_a, variable_b, direction, df)

    if key == "screentime_categories_link":
        al = SCREENTIME_LABELS[variable_a]
        bl = SCREENTIME_LABELS[variable_b]
        pct = _same_side_of_median_pct(df, variable_a, variable_b)
        if not _finite(pct):
            return _fallback_screentime_link(template, direction, al, bl)
        if direction == "negative":
            pct = 100.0 - pct
        title = (
            template.title_positive if direction == "positive"
            else template.title_negative
        ).format(screen_a_title=al["title"], screen_b_noun=bl["noun"])
        if pct >= 99.5:
            body = (
                f"{al['title']} and {bl['noun']} have lined up on every "
                "logged day."
                if direction == "positive"
                else f"{al['title']} and {bl['noun']} have traded off on "
                "every logged day."
            )
            return title, body
        if pct < 1:
            body = (
                f"{al['title']} and {bl['noun']} rarely line up on the same "
                "side of average."
                if direction == "positive"
                else f"{al['title']} and {bl['noun']} almost always move "
                "together rather than trading off."
            )
            return title, body
        return _format_pair(template, direction, {
            "screen_a_title": al["title"],
            "screen_b_noun": bl["noun"],
            "pct": pct,
        })

    if key == "activity_shifts_screentime":
        act = variable_a if variable_a in ACTIVITY_LABELS else variable_b
        scr = variable_b if act == variable_a else variable_a
        al, sl = ACTIVITY_LABELS[act], SCREENTIME_LABELS[scr]
        m_yes, m_no = _binary_continuous_means(df, act, scr)
        if not _finite(m_yes, m_no):
            return _fallback_activity_screentime(template, direction, al, sl)
        return _format_pair(template, direction, {
            "activity_title": al["title"],
            "activity_verb_past": al["verb_past"],
            "screen_title": sl["title"],
            "screen_noun": sl["noun"],
            "m_yes": m_yes,
            "m_no": m_no,
        })

    raise ValueError(f"Unknown template key: {key}")


def _format_pair(
    template: InsightTemplate, direction: str, values: dict
) -> tuple[str, str]:
    if direction == "positive":
        return (
            template.title_positive.format(**values),
            template.body_positive.format(**values),
        )
    return (
        template.title_negative.format(**values),
        template.body_negative.format(**values),
    )


def _render_weekend_shift(
    template: InsightTemplate,
    variable_a: str,
    variable_b: str,
    direction: str,
    df: pd.DataFrame,
) -> tuple[str, str]:
    """Outcome subtype uses mean diff (1–10 scale); screentime subtype uses a
    ratio (minutes scale reads more naturally as 'X× higher')."""
    other = variable_a if variable_a != "is_weekend" else variable_b
    is_outcome = other in OUTCOME_LABELS
    other_meta = OUTCOME_LABELS[other] if is_outcome else SCREENTIME_LABELS[other]

    title_template = (
        template.title_positive if direction == "positive" else template.title_negative
    )
    title = title_template.format(other_lower=other_meta["noun"])

    m_wknd, m_wkdy = _binary_continuous_means(df, "is_weekend", other)
    if not _finite(m_wknd, m_wkdy):
        body = (
            f"Your {other_meta['noun']} runs higher on weekends than weekdays."
            if direction == "positive"
            else f"Your {other_meta['noun']} runs higher on weekdays than weekends."
        )
        return title, body

    if is_outcome:
        body_template = (
            template.body_positive if direction == "positive" else template.body_negative
        )
        body = body_template.format(
            other_title=other_meta["title"], m_wknd=m_wknd, m_wkdy=m_wkdy,
        )
        return title, body

    high, low = (m_wknd, m_wkdy) if direction == "positive" else (m_wkdy, m_wknd)
    high_part = "weekends" if direction == "positive" else "weekdays"
    low_part = "weekdays" if direction == "positive" else "weekends"
    if low <= 0 or not math.isfinite(high / low):
        body = f"{other_meta['title']} runs higher on {high_part} than {low_part}."
    else:
        body = (
            f"{other_meta['title']} runs ~{high / low:.1f}× higher on "
            f"{high_part} than {low_part}."
        )
    return title, body


# --- Fallback bodies (used when the metric can't be computed) -------------

def _fallback_mood_energy(template: InsightTemplate, direction: str) -> tuple[str, str]:
    title = template.title_positive if direction == "positive" else template.title_negative
    body = (
        "Mood and energy track each other day-to-day."
        if direction == "positive"
        else "Mood and energy tend to move in opposite directions."
    )
    return title, body


def _fallback_activity_outcome(
    template: InsightTemplate, direction: str, al: dict, ol: dict
) -> tuple[str, str]:
    t = template.title_positive if direction == "positive" else template.title_negative
    title = t.format(activity_title=al["title"], outcome_lower=ol["noun"])
    verb = "higher" if direction == "positive" else "lower"
    body = f"Your {ol['noun']} tends to be {verb} on days you {al['verb_past']}."
    return title, body


def _fallback_screentime_outcome(
    template: InsightTemplate, direction: str, sl: dict, ol: dict
) -> tuple[str, str]:
    t = template.title_positive if direction == "positive" else template.title_negative
    title = t.format(screen_title=sl["title"], outcome_lower=ol["noun"])
    verb = "higher" if direction == "positive" else "lower"
    body = f"More {sl['noun']} tends to come with {verb} {ol['noun']}."
    return title, body


def _fallback_habits_pair(
    template: InsightTemplate, direction: str, al: dict, bl: dict
) -> tuple[str, str]:
    t = template.title_positive if direction == "positive" else template.title_negative
    title = t.format(activity_a_title=al["title"], activity_b_noun=bl["noun"])
    body = (
        f"You usually {bl['verb_past']} on days you {al['verb_past']}."
        if direction == "positive"
        else f"You rarely {bl['verb_past']} on days you {al['verb_past']}."
    )
    return title, body


def _fallback_screentime_link(
    template: InsightTemplate, direction: str, al: dict, bl: dict
) -> tuple[str, str]:
    t = template.title_positive if direction == "positive" else template.title_negative
    title = t.format(screen_a_title=al["title"], screen_b_noun=bl["noun"])
    body = (
        f"More {al['noun']} tends to come with more {bl['noun']}."
        if direction == "positive"
        else f"More {al['noun']} tends to come with less {bl['noun']}."
    )
    return title, body


def _fallback_activity_screentime(
    template: InsightTemplate, direction: str, al: dict, sl: dict
) -> tuple[str, str]:
    t = template.title_positive if direction == "positive" else template.title_negative
    title = t.format(activity_title=al["title"], screen_noun=sl["noun"])
    verb = "higher" if direction == "positive" else "lower"
    body = f"Your {sl['noun']} tends to be {verb} on days you {al['verb_past']}."
    return title, body


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
            df,
        )
        topic, category = categorize_insight(
            template_key, row.variable_a, row.variable_b
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
                topic=topic,
                category=category,
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
            existing.topic = topic
            existing.category = category
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
