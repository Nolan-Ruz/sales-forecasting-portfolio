"""
Fit, tune, and backtest Prophet models per (store, item) series.

The tuning story this module supports: start from Prophet defaults, then
grid-search `changepoint_prior_scale` and `seasonality_prior_scale` using
Prophet's own rolling-origin cross-validation, and pick the combination with
the lowest backtested MAPE. Because we have 500 series, notebook 02 typically
tunes on a handful of representative series and applies the winning params
broadly, then documents which series (if any) need their own tune.
"""
from __future__ import annotations

import itertools
from dataclasses import dataclass, field

import pandas as pd
from prophet import Prophet
from prophet.diagnostics import cross_validation, performance_metrics

DEFAULT_GRID = {
    "changepoint_prior_scale": [0.01, 0.05, 0.1, 0.5],
    "seasonality_prior_scale": [0.1, 1.0, 10.0],
}


@dataclass
class TuneResult:
    best_params: dict
    grid_results: pd.DataFrame
    model: Prophet


def fit_prophet(
    train: pd.DataFrame,
    country_holidays: str | None = "US",
    weekly_seasonality: bool = True,
    yearly_seasonality: bool = True,
    **prophet_kwargs,
) -> Prophet:
    """Fit a single Prophet model. `train` must have `ds`/`y` columns."""
    model = Prophet(
        weekly_seasonality=weekly_seasonality,
        yearly_seasonality=yearly_seasonality,
        **prophet_kwargs,
    )
    if country_holidays:
        model.add_country_holidays(country_name=country_holidays)
    model.fit(train)
    return model


def grid_search_cv(
    train: pd.DataFrame,
    grid: dict[str, list[float]] = DEFAULT_GRID,
    initial: str = "730 days",
    period: str = "90 days",
    horizon: str = "30 days",
    parallel: str | None = "processes",
) -> TuneResult:
    """
    Rolling-origin cross-validation grid search, per Prophet's recommended
    tuning pattern (https://facebook.github.io/prophet/docs/diagnostics.html).

    `initial`/`period`/`horizon` control the CV cutoffs — defaults assume a
    multi-year daily series (this dataset spans 2013-2017): 2 years of
    history before the first cutoff, a new cutoff every 90 days, forecasting
    30 days ahead each time.
    """
    keys = list(grid.keys())
    combinations = list(itertools.product(*grid.values()))
    rows = []
    best_mape = float("inf")
    best_params = None
    best_model = None

    for combo in combinations:
        params = dict(zip(keys, combo))
        model = fit_prophet(train, **params)
        df_cv = cross_validation(
            model, initial=initial, period=period, horizon=horizon, parallel=parallel
        )
        df_perf = performance_metrics(df_cv, rolling_window=1)
        mape = df_perf["mape"].mean()
        rows.append({**params, "mape": mape, "mae": df_perf["mae"].mean()})
        if mape < best_mape:
            best_mape = mape
            best_params = params
            best_model = model

    grid_results = pd.DataFrame(rows).sort_values("mape").reset_index(drop=True)
    return TuneResult(best_params=best_params, grid_results=grid_results, model=best_model)


def forecast(model: Prophet, periods: int, freq: str = "D") -> pd.DataFrame:
    """Generate a forecast dataframe with yhat/yhat_lower/yhat_upper."""
    future = model.make_future_dataframe(periods=periods, freq=freq)
    fcst = model.predict(future)
    return fcst[["ds", "yhat", "yhat_lower", "yhat_upper"]]


def export_forecast_table(
    fcst: pd.DataFrame, store: int, item: int, actuals: pd.DataFrame | None = None
) -> pd.DataFrame:
    """
    Tag a forecast with store/item keys and (optionally) join actuals, in the
    tidy long format the Power BI fact table expects — see powerbi/README.md.
    """
    out = fcst.copy()
    out["store"] = store
    out["item"] = item
    if actuals is not None:
        out = out.merge(actuals.rename(columns={"y": "actual"}), on="ds", how="left")
    return out
