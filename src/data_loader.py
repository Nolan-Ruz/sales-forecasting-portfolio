"""
Load and reshape the Store Item Demand Forecasting dataset.

Raw file has one row per (date, store, item) with a `sales` count. Prophet
wants one dataframe per series with columns `ds` (date) and `y` (target), so
most of this module is about slicing the long raw table into per-(store, item)
series and adding the calendar scaffolding Prophet/the tuning notebook need.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

RAW_COLUMNS = ["date", "store", "item", "sales"]

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
RAW_PATH = DATA_DIR / "raw" / "train.csv"
PROCESSED_DIR = DATA_DIR / "processed"


def load_raw(path: Path = RAW_PATH) -> pd.DataFrame:
    """Load the raw Kaggle CSV and do basic type coercion / sanity checks."""
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. See data/README.md for download instructions."
        )
    df = pd.read_csv(path, parse_dates=["date"])
    missing_cols = set(RAW_COLUMNS) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Unexpected schema, missing columns: {missing_cols}")
    if (df["sales"] < 0).any():
        raise ValueError("Found negative sales values — data quality issue.")
    return df.sort_values(["store", "item", "date"]).reset_index(drop=True)


def get_series(df: pd.DataFrame, store: int, item: int) -> pd.DataFrame:
    """Return a single (store, item) time series in Prophet's `ds`/`y` format."""
    series = df[(df["store"] == store) & (df["item"] == item)].copy()
    series = series.rename(columns={"date": "ds", "sales": "y"})
    return series[["ds", "y"]].reset_index(drop=True)


def list_series_keys(df: pd.DataFrame) -> list[tuple[int, int]]:
    """All (store, item) combinations present in the dataset (500 for this dataset)."""
    return list(df[["store", "item"]].drop_duplicates().itertuples(index=False, name=None))


def train_test_split_by_date(df: pd.DataFrame, cutoff: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Time-based split (never shuffle time series data). `cutoff` is inclusive
    end date of the training window, e.g. "2017-06-30" holds out ~6 months
    for backtesting.
    """
    cutoff_ts = pd.Timestamp(cutoff)
    train = df[df["ds"] <= cutoff_ts].reset_index(drop=True)
    test = df[df["ds"] > cutoff_ts].reset_index(drop=True)
    return train, test


def save_processed(df: pd.DataFrame, name: str) -> Path:
    """Write a tidy intermediate table to data/processed/ as parquet."""
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PROCESSED_DIR / f"{name}.parquet"
    df.to_parquet(out_path, index=False)
    return out_path
