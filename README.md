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
do we need, and when do we reorder?* This project walks the full chain from raw
sales data to an actionable, self-updating reorder queue:

```
raw daily sales  →  tuned Prophet forecast (+ uncertainty intervals)
                 →  Monte Carlo inventory simulation (service level vs. safety stock)
                 →  auto min/max reorder point + reorder qty per SKU
                 →  Power BI dashboard (forecast accuracy, inventory risk, reorder queue)
```

The pipeline, the inventory/reorder logic, and the dashboard are all complete and
run end to end on the dataset below.

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
├── outputs/                   # tidy CSV tables feeding Power BI
├── powerbi/                   # Power BI project + dashboard screenshots
├── docs/                      # architecture notes, write-up
├── requirements.txt
└── README.md
```

## Running it

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Then follow [`data/README.md`](data/README.md) to fetch the dataset, and run the
notebooks in order (01 → 04). Each notebook writes its output to `outputs/`, which
the Power BI dashboard reads from — see [`powerbi/README.md`](powerbi/README.md).

If notebook imports break after a Python reinstall or upgrade, recreate the
environment rather than debugging the old one: `python -m venv .venv --clear && pip
install -r requirements.txt`, and confirm the notebook's Jupyter kernel points at
this project's venv rather than a system Python.

## Power BI dashboard

The dashboard is delivered as a **Power BI Project (`.pbip`)** rather than a `.pbix`
— the semantic model and report layout are stored as plain text, so the data model
and DAX measures are readable directly in the repo rather than locked inside a
binary file. See [`powerbi/README.md`](powerbi/README.md) for what each page shows.
