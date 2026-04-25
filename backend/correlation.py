"""Pairwise correlation engine over the daily aggregation DataFrame.

Tests every pair of behavioral variables (mood, energy, screen-time categories,
activity flags, is_weekend), filters by sample size, statistical significance
(p-value), and practical significance (|r|), and returns a ranked DataFrame.
"""

from typing import Optional, get_args

import numpy as np
import pandas as pd
from scipy import stats

from schemas import Activity

_DEFAULT_VARIABLES: list[str] = [
    "mood",
    "energy",
    "social_screen_time",
    "entertainment_screen_time",
    "productivity_screen_time",
    "total_screen_time",
    "is_weekend",
    *[f"did_{a}" for a in get_args(Activity)],
]

_RESULT_COLUMNS: list[str] = [
    "variable_a",
    "variable_b",
    "method",
    "r",
    "abs_r",
    "p_value",
    "n",
    "direction",
]


def analyze_correlations(
    df: pd.DataFrame,
    method: str = "spearman",
    min_n: int = 14,
    max_p: float = 0.05,
    min_abs_r: float = 0.3,
    variables: Optional[list[str]] = None,
) -> pd.DataFrame:
    """Return a ranked frame of statistically + practically significant pairs.

    method:    "spearman" (rank-based, robust, default) or "pearson" (linear).
    min_n:     skip pairs with fewer than this many overlapping non-null rows.
    max_p:     drop results with p-value above this threshold.
    min_abs_r: drop results whose |r| is below this effect-size threshold.
    variables: override the default variable set. Missing columns are ignored.
    """
    if method not in ("spearman", "pearson"):
        raise ValueError(f"method must be 'spearman' or 'pearson', got {method!r}")

    cols = [v for v in (variables or _DEFAULT_VARIABLES) if v in df.columns]

    rows = []
    for i, a in enumerate(cols):
        for b in cols[i + 1:]:
            # Pairwise dropna — don't shrink the sample using unrelated columns.
            sub = df[[a, b]].dropna()
            n = len(sub)
            if n < min_n:
                continue
            x = pd.to_numeric(sub[a], errors="coerce").to_numpy(dtype=float)
            y = pd.to_numeric(sub[b], errors="coerce").to_numpy(dtype=float)
            # Constant column → no variance → correlation undefined.
            if np.all(x == x[0]) or np.all(y == y[0]):
                continue

            res = stats.spearmanr(x, y) if method == "spearman" else stats.pearsonr(x, y)
            r = float(res.statistic)
            p = float(res.pvalue)

            rows.append({
                "variable_a": a,
                "variable_b": b,
                "method": method,
                "r": r,
                "abs_r": abs(r),
                "p_value": p,
                "n": n,
                "direction": "positive" if r > 0 else ("negative" if r < 0 else "none"),
            })

    result = pd.DataFrame(rows, columns=_RESULT_COLUMNS)
    if result.empty:
        return result

    result = result[(result["p_value"] <= max_p) & (result["abs_r"] >= min_abs_r)]
    return result.sort_values("abs_r", ascending=False, ignore_index=True)
