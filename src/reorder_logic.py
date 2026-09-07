"""
Auto min/max reorder point logic, built on top of the inventory simulation.

Terminology (continuous review / min-max system):
  - reorder point (min): inventory level that triggers a new order
  - order quantity: how much to order once triggered (here, EOQ)
  - max level: reorder point + order quantity (the level right after receiving
    a full replenishment)

This module is deliberately data-source-agnostic about "on-hand inventory" —
the public dataset has no inventory ledger, only sales, so notebook 04
generates a synthetic-but-clearly-labeled on-hand position for demo purposes
via `simulate_synthetic_on_hand`. Everything else here is real logic that
would plug into an actual inventory feed unchanged.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def reorder_point(expected_lead_time_demand: float, safety_stock: float) -> float:
    """Classic ROP = expected demand during lead time + safety stock buffer."""
    return expected_lead_time_demand + safety_stock


def economic_order_quantity(
    annual_demand: float, order_cost: float, holding_cost_per_unit: float
) -> float:
    """
    EOQ = sqrt(2 * D * S / H)
      D = annual demand (units/year)
      S = fixed cost per order (setup/ordering cost)
      H = holding cost per unit per year
    """
    if annual_demand <= 0 or holding_cost_per_unit <= 0:
        return 0.0
    return float(np.sqrt(2 * annual_demand * order_cost / holding_cost_per_unit))

def min_max_levels(rop: float, eoq: float) -> tuple[float, float]:
    """Min level = reorder point, max level = reorder point + order quantity."""
    return rop, rop + eoq


def simulate_synthetic_on_hand(
    series_keys: list[tuple[int, int]],
    expected_demand_lookup: dict[tuple[int, int], float],
    random_state: int | None = 42,
    coverage_days_range: tuple[int, int] = (5, 45),
) -> pd.DataFrame:
    """
    SYNTHETIC DEMO DATA ONLY. Generates a plausible starting on-hand position
    per (store, item) as `coverage_days` worth of expected daily demand, so
    the reorder table has something realistic to evaluate against. Replace
    with a real inventory feed in a production setting.
    """
    rng = np.random.default_rng(random_state)
    rows = []
    for store, item in series_keys:
        daily_demand = expected_demand_lookup.get((store, item), 0.0)
        coverage_days = rng.integers(*coverage_days_range)
        rows.append(
            {"store": store, "item": item, "on_hand": daily_demand * coverage_days}
        )
    return pd.DataFrame(rows)


def build_reorder_table(
    sim_results: pd.DataFrame,
    on_hand: pd.DataFrame,
    order_cost: float = 50.0,
    holding_cost_per_unit: float = 2.0,
    days_per_year: int = 365,
) -> pd.DataFrame:
    """
    Combine per-series Monte Carlo simulation results (from inventory_sim.py)
    with on-hand inventory into the final reorder recommendation table that
    feeds the Power BI "Reorder Queue" page.

    `sim_results` columns expected: store, item, expected_lead_time_demand,
    safety_stock (as produced by inventory_sim.simulate_for_series).
    `on_hand` columns expected: store, item, on_hand.
    """
    df = sim_results.merge(on_hand, on=["store", "item"], how="left")
    df["on_hand"] = df["on_hand"].fillna(0.0)

    # Approximate annual demand from the (short) lead-time-window expected
    # demand — scaled up; notebook 04 documents this and can substitute a
    # trailing-12-month actuals sum instead once available.
    daily_rate = df["expected_lead_time_demand"] / df["lead_time_days"]
    annual_demand = daily_rate * days_per_year

    df["reorder_point"] = reorder_point(df["expected_lead_time_demand"], df["safety_stock"])
    df["eoq"] = [
        economic_order_quantity(d, order_cost, holding_cost_per_unit) for d in annual_demand
    ]
    df["min_level"], df["max_level"] = zip(*[
        min_max_levels(rop, eoq) for rop, eoq in zip(df["reorder_point"], df["eoq"])
    ])
    df["needs_reorder"] = df["on_hand"] < df["reorder_point"]
    df["suggested_order_qty"] = np.where(
        df["needs_reorder"], df["max_level"] - df["on_hand"], 0.0
    )
    return df
