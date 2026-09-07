# Sales Forecasting, Inventory Simulation & Auto Reorder System

Portfolio recreation of a demand-forecasting system: tuning a **Prophet** time-series
model on daily store/item sales, then building two downstream decision-support tools
on top of the forecast — a **Monte Carlo inventory simulation** and **automatic
min/max reorder point logic** — surfaced in a **Power BI** dashboard.

> This is a from-scratch rebuild for portfolio purposes using a public dataset. No
> proprietary data, code, or business logic from any previous employer is used —
> the modeling approach (tuning workflow, inventory math, reorder logic) is
> reimplemented independently.

## Why this project

Forecasting sales is only half the problem — the operational payoff is turning a
forecast (with its uncertainty) into an inventory decision: *how much safety stock
do we need, and when do we reorder?* This project walks the full chain:

```
raw daily sales  →  tuned Prophet forecast (+ uncertainty intervals)
                 →  Monte Carlo inventory simulation (service level vs. safety stock)
                 →  auto min/max reorder point + reorder qty per SKU
                 →  Power BI dashboard (forecast accuracy, inventory risk, reorder queue)
```

## Dataset

[Kaggle: Store Item Demand Forecasting Challenge](https://www.kaggle.com/competitions/demand-forecasting-kernels-only/data)
— daily unit sales for 10 stores × 50 items, 2013–2017. Chosen over store-level-only
datasets (Rossmann, Walmart) because it has **item-level granularity**, which the
inventory simulation and reorder logic require (those only make sense per-SKU).

See [`data/README.md`](data/README.md) for download instructions.

## Repo structure

```
sales-forecasting-portfolio/
├── data/
│   ├── raw/                  # downloaded Kaggle CSV (gitignored)
│   └── processed/            # cleaned/reshaped parquet (gitignored)
├── notebooks/
│   ├── 01_eda.ipynb                    # trend/seasonality/variability exploration
│   ├── 02_prophet_forecasting.ipynb    # baseline -> tuned Prophet, backtesting
│   ├── 03_inventory_simulation.ipynb   # Monte Carlo demand sim, safety stock
│   └── 04_reorder_minmax_logic.ipynb   # auto min/max + reorder qty per SKU
├── src/
│   ├── data_loader.py         # load/clean/reshape raw data
│   ├── prophet_pipeline.py    # fit/tune/cross-validate Prophet, forecast export
│   ├── inventory_sim.py       # Monte Carlo simulation over forecast distribution
│   └── reorder_logic.py       # min/max/reorder-point calculations
├── outputs/                   # tidy CSV/Parquet tables feeding Power BI
├── powerbi/                   # .pbix file + dashboard screenshots/GIF
├── docs/                      # architecture notes, write-up
├── requirements.txt
└── README.md
```

## Setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Then follow [`data/README.md`](data/README.md) to fetch the dataset, and run the
notebooks in order (01 → 04).

## Roadmap

- [ ] **01 — EDA**: seasonality decomposition, per-SKU demand variability, stationarity checks
- [ ] **02 — Prophet tuning**: baseline model, holiday regressors, `cross_validation`/
      `performance_metrics` grid search over `changepoint_prior_scale` /
      `seasonality_prior_scale`, backtested MAPE/MAE
- [ ] **03 — Inventory simulation**: Monte Carlo demand draws from forecast uncertainty,
      safety stock vs. service-level tradeoff curves
- [ ] **04 — Auto min/max reorder logic**: reorder point, min/max levels, reorder qty
      recommendation table, recalculated per forecast refresh
- [ ] **Power BI dashboard**: Forecast Accuracy / Inventory Risk / Reorder Queue pages
      built on `outputs/` tables
- [ ] **Polish**: architecture diagram, dashboard screenshots/GIF, write-up in `docs/`

## Power BI dashboard

See [`powerbi/README.md`](powerbi/README.md) for the data model and page wireframes.
Since `.pbix` files don't render on GitHub, the repo includes exported screenshots/GIF
of the live dashboard alongside the file itself.
