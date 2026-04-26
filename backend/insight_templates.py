"""Natural-language templates for turning correlation results into insights.

A small, hand-tuned set of templates that map a row from
`correlation.analyze_correlations` to a short, discovery-feeling message with
a title and a body. Direction (positive vs negative) is handled per-template
so the language fits the finding instead of being hedged.

Not a pipeline — no template-selection logic and no rendering helpers beyond
`confidence_from_p`. A future generator module will:
  1. Pick the right template for a given pair (based on variable types).
  2. Resolve placeholders using the label maps below (or a tuned version).
  3. Format with `.format(**values)` and emit the final strings.
"""

from dataclasses import dataclass


# --- Confidence indicator -------------------------------------------------

@dataclass(frozen=True)
class Confidence:
    stars: str        # glanceable visual: "★★", "★★★", "★★★★"
    label: str        # short adjective for inline use: "moderate", "strong", "very strong"
    long_label: str   # full phrase that drops into a body sentence


def confidence_from_p(p: float) -> Confidence:
    """Map a p-value to a 3-bucket evidence indicator. Engine already
    filters to p ≤ 0.05, so the floor is "moderate"."""
    if p < 0.001:
        return Confidence("★★★★", "very strong", "Very strong evidence")
    if p < 0.01:
        return Confidence("★★★",  "strong",      "Strong evidence")
    return Confidence("★★",       "moderate",    "Moderate evidence")


# --- Display label maps ---------------------------------------------------
# Starting point. Tune to match the app's voice; the generator should look
# variable names up here when filling template placeholders.

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

OUTCOME_LABELS: dict[str, str] = {"mood": "mood", "energy": "energy"}


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
        title_positive="{activity_title} lifts your {outcome}",
        body_positive=(
            "On the {n} days you {activity_verb_past}, your {outcome} ran "
            "noticeably higher than on the days you didn't. {confidence_long} "
            "({confidence_stars})."
        ),
        title_negative="{activity_title} costs you {outcome}",
        body_negative=(
            "Days you {activity_verb_past} tended to come with lower {outcome}. "
            "The dip held up across {n} days — {confidence_long} "
            "({confidence_stars})."
        ),
        example_positive=(
            "Title: Exercise lifts your mood\n"
            "Body:  On the 42 days you exercised, your mood ran noticeably "
            "higher than on the days you didn't. Very strong evidence (★★★★)."
        ),
        example_negative=(
            "Title: Gaming costs you energy\n"
            "Body:  Days you gamed tended to come with lower energy. The dip "
            "held up across 38 days — Moderate evidence (★★)."
        ),
    ),

    # 2. Screen-time category × mood/energy. "More of X = more/less of Y"
    #    framing without exposing raw r.
    InsightTemplate(
        key="screentime_affects_outcome",
        pattern="One screen-time category (continuous minutes) paired with mood or energy.",
        title_positive="{screen_title} pairs with higher {outcome}",
        body_positive=(
            "More {screen_noun} tended to come with higher {outcome} — a "
            "consistent pattern across {n} days. {confidence_long} "
            "({confidence_stars})."
        ),
        title_negative="{screen_title} is weighing on your {outcome}",
        body_negative=(
            "More {screen_noun} tended to drag your {outcome} down — a clear "
            "pattern across {n} days. {confidence_long} ({confidence_stars})."
        ),
        example_positive=(
            "Title: Productivity-app time pairs with higher energy\n"
            "Body:  More productivity-app time tended to come with higher "
            "energy — a consistent pattern across 55 days. Strong evidence (★★★)."
        ),
        example_negative=(
            "Title: Entertainment time is weighing on your mood\n"
            "Body:  More entertainment time tended to drag your mood down — a "
            "clear pattern across 62 days. Strong evidence (★★★)."
        ),
    ),

    # 3. The only outcome × outcome pair. Specific phrasing because "your mood
    #    and energy move together" reads warmer than the generic version.
    InsightTemplate(
        key="mood_energy_couple",
        pattern="Specifically mood × energy.",
        title_positive="Your mood and energy move together",
        body_positive=(
            "When one is up, the other usually is too — they rose and fell in "
            "sync across {n} days. {confidence_long} ({confidence_stars})."
        ),
        title_negative="Your mood and energy pull opposite",
        body_negative=(
            "When one rises, the other tends to fall — an unusual but "
            "consistent pattern across {n} days. {confidence_long} "
            "({confidence_stars})."
        ),
        example_positive=(
            "Title: Your mood and energy move together\n"
            "Body:  When one is up, the other usually is too — they rose and "
            "fell in sync across 70 days. Very strong evidence (★★★★)."
        ),
        example_negative=(
            "Title: Your mood and energy pull opposite\n"
            "Body:  When one rises, the other tends to fall — an unusual but "
            "consistent pattern across 28 days. Moderate evidence (★★)."
        ),
    ),

    # 4. Two activity flags. Co-occurrence (positive r) or mutual exclusion
    #    (negative r) of behaviors.
    InsightTemplate(
        key="habits_pair",
        pattern="Two activity flags (did_* × did_*).",
        title_positive="{activity_a_title} and {activity_b_noun} come as a pair",
        body_positive=(
            "Most days you {activity_a_verb_past}, you also {activity_b_verb_past} — "
            "a tight pairing across {n} days. {confidence_long} "
            "({confidence_stars})."
        ),
        title_negative="{activity_a_title} and {activity_b_noun} rarely overlap",
        body_negative=(
            "On days you {activity_a_verb_past}, you usually didn't "
            "{activity_b_verb_past} — a clear split across {n} days. "
            "{confidence_long} ({confidence_stars})."
        ),
        example_positive=(
            "Title: Exercise and outdoor time come as a pair\n"
            "Body:  Most days you exercised, you also went outdoors — a tight "
            "pairing across 47 days. Very strong evidence (★★★★)."
        ),
        example_negative=(
            "Title: Reading and gaming rarely overlap\n"
            "Body:  On days you read, you usually didn't game — a clear split "
            "across 50 days. Strong evidence (★★★)."
        ),
    ),

    # 5. is_weekend × {mood, energy, screen-time}. Reframes the correlation as
    #    a weekday/weekend contrast. (is_weekend × activity is not handled —
    #    the generator should fall through to a generic template for that.)
    InsightTemplate(
        key="weekend_shift",
        pattern="is_weekend paired with mood, energy, or any screen-time category.",
        title_positive="Weekends lift your {other_lower}",
        body_positive=(
            "Your {other_noun} runs higher on Saturdays and Sundays than the "
            "rest of the week — the pattern held over {n} days. "
            "{confidence_long} ({confidence_stars})."
        ),
        title_negative="Weekdays carry your {other_lower}",
        body_negative=(
            "Your {other_noun} runs higher Monday through Friday than on "
            "weekends — the pattern held over {n} days. {confidence_long} "
            "({confidence_stars})."
        ),
        example_positive=(
            "Title: Weekends lift your mood\n"
            "Body:  Your mood runs higher on Saturdays and Sundays than the "
            "rest of the week — the pattern held over 60 days. Very strong "
            "evidence (★★★★)."
        ),
        example_negative=(
            "Title: Weekdays carry your productivity-app time\n"
            "Body:  Your productivity-app time runs higher Monday through "
            "Friday than on weekends — the pattern held over 55 days. Strong "
            "evidence (★★★)."
        ),
    ),

    # 6. Two screen-time categories. Spots usage clusters (rise together) or
    #    trade-offs (one up, the other down).
    InsightTemplate(
        key="screentime_categories_link",
        pattern="Two screen-time categories (e.g., social_screen_time × entertainment_screen_time).",
        title_positive="{screen_a_title} and {screen_b_noun} rise together",
        body_positive=(
            "When one climbs, the other usually does too — the two moved "
            "together across {n} days. {confidence_long} ({confidence_stars})."
        ),
        title_negative="{screen_a_title} trades off with {screen_b_noun}",
        body_negative=(
            "Days with more {screen_a_noun} came with less {screen_b_noun} "
            "and vice versa — a clear trade-off across {n} days. "
            "{confidence_long} ({confidence_stars})."
        ),
        example_positive=(
            "Title: Social-app time and entertainment time rise together\n"
            "Body:  When one climbs, the other usually does too — the two "
            "moved together across 50 days. Strong evidence (★★★)."
        ),
        example_negative=(
            "Title: Productivity-app time trades off with entertainment time\n"
            "Body:  Days with more productivity-app time came with less "
            "entertainment time and vice versa — a clear trade-off across 44 "
            "days. Strong evidence (★★★)."
        ),
    ),

    # 7. Activity flag × screen-time category. Cross-domain link between a
    #    behavior and screen-use.
    InsightTemplate(
        key="activity_shifts_screentime",
        pattern="One activity flag paired with one screen-time category.",
        title_positive="{activity_title} days run heavier on {screen_noun}",
        body_positive=(
            "On the {n} days you {activity_verb_past}, your {screen_noun} "
            "tended to be noticeably higher than usual. {confidence_long} "
            "({confidence_stars})."
        ),
        title_negative="{activity_title} days come with less {screen_noun}",
        body_negative=(
            "On the {n} days you {activity_verb_past}, your {screen_noun} "
            "tended to be noticeably lower than usual. {confidence_long} "
            "({confidence_stars})."
        ),
        example_positive=(
            "Title: Gaming days run heavier on entertainment time\n"
            "Body:  On the 32 days you gamed, your entertainment time tended "
            "to be noticeably higher than usual. Strong evidence (★★★)."
        ),
        example_negative=(
            "Title: Exercise days come with less total screen time\n"
            "Body:  On the 40 days you exercised, your total screen time "
            "tended to be noticeably lower than usual. Strong evidence (★★★)."
        ),
    ),
]
