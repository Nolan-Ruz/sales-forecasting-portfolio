# Data acquisition

Dataset: [Store Item Demand Forecasting Challenge](https://www.kaggle.com/competitions/demand-forecasting-kernels-only/data)
(Kaggle). Daily unit sales, 10 stores × 50 items, 2013-01-01 through 2017-12-31.
Columns: `date`, `store`, `item`, `sales`.

Raw and processed data are gitignored — this dataset is a Kaggle competition
dataset and shouldn't be redistributed via the repo; anyone cloning this project
downloads it themselves (free, ~2 minutes).

## Option A — Kaggle web UI (no setup)

1. Create a free Kaggle account if you don't have one.
2. Go to the [competition data page](https://www.kaggle.com/competitions/demand-forecasting-kernels-only/data)
   and click "Join Competition" (required to unlock downloads — it's a closed/inactive
   competition, no submission needed) then **Download All**.
3. Unzip and place `train.csv` into `data/raw/train.csv`.

## Option B — Kaggle CLI

```powershell
pip install kaggle
# Get an API token: Kaggle account settings -> "Create New Token" -> downloads kaggle.json
# Place it at %USERPROFILE%\.kaggle\kaggle.json

kaggle competitions download -c demand-forecasting-kernels-only -p data\raw
Expand-Archive data\raw\demand-forecasting-kernels-only.zip -DestinationPath data\raw
```

You should end up with `data/raw/train.csv` (and `test.csv`, unused here — the
competition test set has no `sales` column since it's a submission target, so all
train/test splitting for backtesting happens inside `train.csv` in notebook 02).

## Verifying the download

Run this after placing the file to confirm shape/columns before opening notebook 01:

```powershell
python -c "import pandas as pd; df = pd.read_csv('data/raw/train.csv'); print(df.shape); print(df.dtypes); print(df.head())"
```

Expected: `(913000, 4)`, columns `date, store, item, sales`.
