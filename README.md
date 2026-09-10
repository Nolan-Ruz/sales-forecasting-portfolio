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
├── powerbi/                   # .pbip project (Report/ + SemanticModel/) + screenshots/GIF
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

### Troubleshooting: notebooks suddenly can't import anything

`.venv` on Windows is a thin shim — it points at wherever the base Python
interpreter it was created from lives (e.g.
`C:\Users\<you>\AppData\Local\Programs\Python\Python312\`) rather than bundling
its own copy. If that base install is later removed or replaced (e.g. by
upgrading Python, or an installer cleanup), `.venv\Scripts\python.exe` stops
working even though all the packages are still sitting in
`.venv\Lib\site-packages`. Symptoms: `ModuleNotFoundError` for packages you
know are installed, or a notebook kernel that resolves to some other, bare
Python install with nothing installed in it.

Fix:

```powershell
py -0p                      # list installed Python versions + paths
```

- If the same Python version the venv was built with (check `.venv\pyvenv.cfg`
  → `version =`) is available again, `.venv` should just start working — no
  reinstall needed.
- If that version is gone for good, reinstall the same major.minor version
  (e.g. via `winget install --id Python.Python.3.12 --version 3.12.10`) rather
  than rebuilding against whatever's newest — this reuses everything already
  installed in `.venv` (including Prophet, which is slow to rebuild) instead
  of a full `pip install -r requirements.txt` from scratch.
- As a last resort, rebuild from scratch: `python -m venv .venv --clear && pip
  install -r requirements.txt`.

Also make sure the notebook's Jupyter kernel is actually the project's venv
(look for **"Python (sales-forecasting-portfolio .venv)"** in the kernel
picker), not a random system Python — that mismatch causes the same symptoms
even when `.venv` itself is fine.

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
The dashboard is committed as a Power BI Project (`.pbip`) rather than a `.pbix` — the
model (TMDL) and report layout (JSON) are plain text, so changes show up as real diffs
instead of an opaque binary. Since a live report still doesn't render on GitHub, the repo
also includes exported screenshots/GIF of the dashboard alongside the project files.
