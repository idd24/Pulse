"""Natural-language templates for turning correlation results into insights.

Each template maps a row from `correlation.analyze_correlations` to a short,
discovery-feeling card with a title and a one-sentence body. Direction
(positive vs negative) is handled per-template so the language fits the
finding instead of being hedged.

Bodies are deliberately terse: one sentence, one concrete number — a group
mean, ratio, or co-occurrence rate computed from the daily DataFrame. The
card UI shows confidence as a badge, so it is intentionally absent from body
text. The numbers themselves are computed in `insights_pipeline._render`
before the template strings are formatted.
"""

from dataclasses import dataclass


# --- Confidence indicator -------------------------------------------------

@dataclass(frozen=True)
class Confidence:
    stars: str        # glanceable visual: "★★", "★★★", "★★★★"
    label: str        # short adjective: "moderate", "strong", "very strong"
    long_label: str   # full phrase suitable for a sentence


def confidence_from_p(p: float) -> Confidence:
    """Map a p-value to a 3-bucket evidence indicator. Engine already
    filters to p ≤ 0.05, so the floor is "moderate"."""
    if p < 0.001:
        return Confidence("★★★★", "very strong", "Very strong evidence")
    if p < 0.01:
        return Confidence("★★★",  "strong",      "Strong evidence")
    return Confidence("★★",       "moderate",    "Moderate evidence")


# --- Display label maps ---------------------------------------------------

ACTIVITY_LABELS: dict[str, dict[str, str]] = {
    "did_exercise":   {"noun": "exercise",      "verb_past": "exercised",    "title": "Exercise"},
    "did_work":       {"noun": "work",          "verb_past": "worked",       "title": "Work"},
    "did_social":     {"noun": "social time",   "verb_past": "socialized",   "title": "Socializing"},
    "did_outdoors":   {"noun": "outdoor time",  "verb_past": "went outdoors","title": "Outdoor time"},
    "did_reading":    {"noun": "reading",       "verb_past": "read",         "title": "Reading"},
    "did_gaming":     {"noun": "gaming",        "verb_past": "gamed",        "title": "Gaming"},
    "did_meditation": {"noun": "meditation",    "verb_past": "meditated",    "title": "Meditation"},
    "did_chores":     {"noun": "chores",        "verb_past": "did chores",   "title": "Chores"},
}

SCREENTIME_LABELS: dict[str, dict[str, str]] = {
    "social_screen_time":        {"noun": "social-app time",       "title": "Social-app time"},
    "entertainment_screen_time": {"noun": "entertainment time",    "title": "Entertainment time"},
    "productivity_screen_time":  {"noun": "productivity-app time", "title": "Productivity-app time"},
    "total_screen_time":         {"noun": "total screen time",     "title": "Total screen time"},
}

OUTCOME_LABELS: dict[str, dict[str, str]] = {
    "mood":   {"noun": "mood",   "title": "Mood"},
    "energy": {"noun": "energy", "title": "Energy"},
}


# --- Categorization (dedup topic + user-facing pill label) ----------------
# `topic` is a machine ID used to dedup near-duplicates at the API surface:
# two rows with the same topic describe the same finding through different
# lenses (e.g. weekend_shift × productivity_screen_time vs.
# activity_shifts_screentime(did_work, productivity_screen_time)), and the
# curator keeps only the strongest. `category` is the short label shown on
# the card so visually similar wording reads as different topics.

CATEGORY_MOOD = "Mood"
CATEGORY_ENERGY = "Energy"
CATEGORY_SCREEN_TIME = "Screen time"
CATEGORY_HABITS = "Habits"
CATEGORY_MOOD_ENERGY = "Mood × Energy"


def _outcome_category(var: str) -> str:
    return CATEGORY_MOOD if var == "mood" else CATEGORY_ENERGY


def categorize_insight(
    template_key: str, variable_a: str, variable_b: str
) -> tuple[str, str]:
    """Return (topic, category) for a generated insight."""
    if template_key == "mood_energy_couple":
        return "mood_energy", CATEGORY_MOOD_ENERGY

    if template_key == "activity_affects_outcome":
        outcome = variable_a if variable_a in OUTCOME_LABELS else variable_b
        return outcome, _outcome_category(outcome)

    if template_key == "screentime_affects_outcome":
        outcome = variable_a if variable_a in OUTCOME_LABELS else variable_b
        return outcome, _outcome_category(outcome)

    if template_key == "weekend_shift":
        other = variable_b if variable_a == "is_weekend" else variable_a
        if other in OUTCOME_LABELS:
            return other, _outcome_category(other)
        return other, CATEGORY_SCREEN_TIME

    if template_key == "habits_pair":
        a, b = sorted((variable_a, variable_b))
        return f"habits:{a}:{b}", CATEGORY_HABITS

    if template_key == "screentime_categories_link":
        a, b = sorted((variable_a, variable_b))
        return f"screen_pair:{a}:{b}", CATEGORY_SCREEN_TIME

    if template_key == "activity_shifts_screentime":
        screen = variable_a if variable_a in SCREENTIME_LABELS else variable_b
        return screen, CATEGORY_SCREEN_TIME

    raise ValueError(f"Unknown template key: {template_key}")


# --- Templates ------------------------------------------------------------

@dataclass(frozen=True)
class InsightTemplate:
    key: str
    pattern: str                # description of which variable pair triggers this
    title_positive: str         # used when r > 0
    body_positive: str
    title_negative: str         # used when r < 0
    body_negative: str
    example_positive: str       # rendered example for review (no placeholders)
    example_negative: str


INSIGHT_TEMPLATES: list[InsightTemplate] = [
    # 1. Activity flag × mood/energy. The most actionable insight type — points
    #    to a behavior the user can repeat or pull back on.
    InsightTemplate(
        key="activity_affects_outcome",
        pattern="One activity flag (did_*) paired with one outcome (mood or energy).",
        title_positive="{activity_title} lifts your {outcome_lower}",
        body_positive=(
            "{outcome_title} averages {m_yes:.1f} on days you "
            "{activity_verb_past} vs {m_no:.1f} on the rest."
        ),
        title_negative="{activity_title} drags down your {outcome_lower}",
        body_negative=(
            "{outcome_title} averages {m_yes:.1f} on days you "
            "{activity_verb_past} vs {m_no:.1f} on the rest."
        ),
        example_positive=(
            "Title: Exercise lifts your mood\n"
            "Body:  Mood averages 7.4 on days you exercised vs 5.8 on the rest."
        ),
        example_negative=(
            "Title: Gaming drags down your energy\n"
            "Body:  Energy averages 5.4 on days you gamed vs 6.8 on the rest."
        ),
    ),

    # 2. Screen-time category × mood/energy. Median-split on screen time, then
    #    contrast outcome means.
    InsightTemplate(
        key="screentime_affects_outcome",
        pattern="One screen-time category (continuous minutes) paired with mood or energy.",
        title_positive="{screen_title} pairs with higher {outcome_lower}",
        body_positive=(
            "{outcome_title} averages {m_high:.1f} on days with more "
            "{screen_noun}, {m_low:.1f} on days with less."
        ),
        title_negative="{screen_title} weighs on your {outcome_lower}",
        body_negative=(
            "{outcome_title} averages {m_high:.1f} on days with more "
            "{screen_noun}, {m_low:.1f} on days with less."
        ),
        example_positive=(
            "Title: Productivity-app time pairs with higher energy\n"
            "Body:  Energy averages 6.4 on days with more productivity-app "
            "time, 5.1 on days with less."
        ),
        example_negative=(
            "Title: Entertainment time weighs on your mood\n"
            "Body:  Mood averages 5.4 on days with more entertainment time, "
            "6.7 on days with less."
        ),
    ),

    # 3. Mood × energy. Specific phrasing because "your mood and energy move
    #    together" reads warmer than the generic version.
    InsightTemplate(
        key="mood_energy_couple",
        pattern="Specifically mood × energy.",
        title_positive="Your mood and energy move together",
        body_positive=(
            "On {pct:.0f}% of days, both land on the same side of average."
        ),
        title_negative="Your mood and energy pull apart",
        body_negative=(
            "On {pct:.0f}% of days, they land on opposite sides of average."
        ),
        example_positive=(
            "Title: Your mood and energy move together\n"
            "Body:  On 81% of days, both land on the same side of average."
        ),
        example_negative=(
            "Title: Your mood and energy pull apart\n"
            "Body:  On 68% of days, they land on opposite sides of average."
        ),
    ),

    # 4. Two activity flags. Co-occurrence (positive) or mutual exclusion
    #    (negative).
    InsightTemplate(
        key="habits_pair",
        pattern="Two activity flags (did_* × did_*).",
        title_positive="{activity_a_title} and {activity_b_noun} go hand in hand",
        body_positive=(
            "On {pct:.0f}% of days you {activity_a_verb_past}, you also "
            "{activity_b_verb_past}."
        ),
        title_negative="{activity_a_title} crowds out {activity_b_noun}",
        body_negative=(
            "Just {pct:.0f}% of days you {activity_a_verb_past} also "
            "include {activity_b_noun}."
        ),
        example_positive=(
            "Title: Exercise and outdoor time go hand in hand\n"
            "Body:  On 78% of days you exercised, you also went outdoors."
        ),
        example_negative=(
            "Title: Reading crowds out gaming\n"
            "Body:  Just 12% of days you read also include gaming."
        ),
    ),

    # 5. is_weekend × {mood, energy, screen-time}. Body shape splits by
    #    subtype: outcomes use a mean comparison (1–10 scale), screen-time
    #    uses a ratio (minutes scale reads better that way). The screen-time
    #    body string is built inside `_render` rather than stored here.
    InsightTemplate(
        key="weekend_shift",
        pattern="is_weekend paired with mood, energy, or any screen-time category.",
        title_positive="Weekends lift your {other_lower}",
        body_positive=(
            "{other_title} averages {m_wknd:.1f} on weekends vs "
            "{m_wkdy:.1f} on weekdays."
        ),
        title_negative="Weekdays drive your {other_lower}",
        body_negative=(
            "{other_title} averages {m_wkdy:.1f} on weekdays vs "
            "{m_wknd:.1f} on weekends."
        ),
        example_positive=(
            "Title: Weekends lift your mood\n"
            "Body:  Mood averages 7.2 on weekends vs 5.8 on weekdays.\n"
            "(Screen-time variant rendered inline: \"Entertainment time runs "
            "~2.1× higher on weekends than weekdays.\")"
        ),
        example_negative=(
            "Title: Weekdays drive your productivity-app time\n"
            "Body:  Productivity-app time runs ~2.4× higher on weekdays "
            "than weekends."
        ),
    ),

    # 6. Two screen-time categories. Same-side-of-median agreement reads
    #    cleaner than raw r without lying about scale.
    InsightTemplate(
        key="screentime_categories_link",
        pattern="Two screen-time categories (e.g., social_screen_time × entertainment_screen_time).",
        title_positive="{screen_a_title} and {screen_b_noun} rise together",
        body_positive=(
            "Both run high (or both run low) on {pct:.0f}% of days."
        ),
        title_negative="{screen_a_title} trades off with {screen_b_noun}",
        body_negative=(
            "One runs high while the other runs low on {pct:.0f}% of days."
        ),
        example_positive=(
            "Title: Social-app time and entertainment time rise together\n"
            "Body:  Both run high (or both run low) on 74% of days."
        ),
        example_negative=(
            "Title: Productivity-app time trades off with entertainment time\n"
            "Body:  One runs high while the other runs low on 71% of days."
        ),
    ),

    # 7. Activity flag × screen-time category. Means in minutes.
    InsightTemplate(
        key="activity_shifts_screentime",
        pattern="One activity flag paired with one screen-time category.",
        title_positive="{activity_title} days run heavy on {screen_noun}",
        body_positive=(
            "{screen_title} averages {m_yes:.0f} min on days you "
            "{activity_verb_past} vs {m_no:.0f} min on the rest."
        ),
        title_negative="{activity_title} days come with less {screen_noun}",
        body_negative=(
            "{screen_title} averages {m_yes:.0f} min on days you "
            "{activity_verb_past} vs {m_no:.0f} min on the rest."
        ),
        example_positive=(
            "Title: Gaming days run heavy on entertainment time\n"
            "Body:  Entertainment time averages 162 min on days you gamed "
            "vs 78 min on the rest."
        ),
        example_negative=(
            "Title: Exercise days come with less total screen time\n"
            "Body:  Total screen time averages 184 min on days you exercised "
            "vs 312 min on the rest."
        ),
    ),
]
