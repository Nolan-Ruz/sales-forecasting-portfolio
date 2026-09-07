"""
Monte Carlo inventory simulation driven by Prophet's forecast uncertainty.

Instead of treating the forecast as a single point estimate, we treat each
day's `yhat` as the mean of a normal distribution whose spread comes from
Prophet's own `yhat_lower`/`yhat_upper` interval. Summing simulated daily
draws over a lead-time window gives a distribution of *lead-time demand* —
which is the quantity safety stock actually needs to protect against, not
next Tuesday's demand in isolation.

Simplifying assumption (documented, not hidden): daily demand draws within a
lead-time window are treated as independent. Real demand has some day-to-day
autocorrelation; this is a reasonable first-order approximation and a natural
"future work" callout in the write-up.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

# Prophet's default uncertainty interval is 80% (interval_width=0.8).
# z-score for the interval half-width, used to back out an implied std dev.
DEFAULT_INTERVAL_WIDTH = 0.8
Z_FOR_DEFAULT_INTERVAL = 1.2816  # scipy.stats.norm.ppf(0.9)


def add_implied_sigma(
    fcst: pd.DataFrame, interval_width: float = DEFAULT_INTERVAL_WIDTH
) -> pd.DataFrame:
    """
    Back out an implied per-day std dev from Prophet's yhat_lower/yhat_upper,
    assuming the interval is symmetric and approximately normal.
    """
    from scipy.stats import norm

    z = norm.ppf(0.5 + interval_width / 2)
    out = fcst.copy()
    out["sigma"] = (out["yhat_upper"] - out["yhat_lower"]) / (2 * z)
    out["sigma"] = out["sigma"].clip(lower=0)
    return out


def simulate_lead_time_demand(
    fcst_with_sigma: pd.DataFrame,
    lead_time_days: int,
    n_sims: int = 10_000,
    random_state: int | None = 42,
) -> np.ndarray:
    """
    Monte Carlo sample total demand over the next `lead_time_days` of the
    forecast window. Returns an array of shape (n_sims,) — one simulated
    total per trial.

    `fcst_with_sigma` must be sorted by `ds` ascending and start at the day
    lead time begins counting from; only the first `lead_time_days` rows
    are used.
    """
    window = fcst_with_sigma.head(lead_time_days)
    if len(window) < lead_time_days:
        raise ValueError(
            f"Forecast window only has {len(window)} rows, need {lead_time_days}"
        )
    rng = np.random.default_rng(random_state)
    means = window["yhat"].to_numpy()
    sigmas = window["sigma"].to_numpy()
    # (n_sims, lead_time_days) draws, one column per day, then sum across days
    draws = rng.normal(loc=means, scale=sigmas, size=(n_sims, lead_time_days))
    draws = np.clip(draws, a_min=0, a_max=None)  # sales can't be negative
    return draws.sum(axis=1)


def safety_stock_for_service_level(
    lead_time_demand_samples: np.ndarray, target_service_level: float
) -> float:
    """
    Safety stock = the inventory buffer above *expected* lead-time demand
    needed to hit `target_service_level` (e.g. 0.95 -> stock out in at most
    5% of replenishment cycles).
    """
    expected_demand = lead_time_demand_samples.mean()
    demand_at_service_level = np.quantile(lead_time_demand_samples, target_service_level)
    return max(demand_at_service_level - expected_demand, 0.0)


def service_level_curve(
    lead_time_demand_samples: np.ndarray,
    service_levels: tuple[float, ...] = (0.80, 0.85, 0.90, 0.95, 0.975, 0.99),
) -> pd.DataFrame:
    """Safety stock required at a range of target service levels — the classic tradeoff chart."""
    rows = [
        {
            "service_level": sl,
            "safety_stock": safety_stock_for_service_level(lead_time_demand_samples, sl),
        }
        for sl in service_levels
    ]
    return pd.DataFrame(rows)


def simulate_for_series(
    fcst: pd.DataFrame,
    store: int,
    item: int,
    lead_time_days: int,
    target_service_level: float,
    n_sims: int = 10_000,
) -> dict:
    """
    End-to-end convenience wrapper: forecast -> implied sigma -> Monte Carlo ->
    safety stock, for one (store, item), in a dict shaped for easy DataFrame
    assembly across many series (used by notebook 03 and the Power BI export).
    """
    fcst_sigma = add_implied_sigma(fcst)
    samples = simulate_lead_time_demand(fcst_sigma, lead_time_days, n_sims=n_sims)
    return {
        "store": store,
        "item": item,
        "lead_time_days": lead_time_days,
        "target_service_level": target_service_level,
        "expected_lead_time_demand": samples.mean(),
        "safety_stock": safety_stock_for_service_level(samples, target_service_level),
        "p95_lead_time_demand": np.quantile(samples, 0.95),
    }
