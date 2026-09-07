# Power BI Dashboard

Built on the CSV/Parquet tables exported by the notebooks into `outputs/`.
Nothing in Power BI re-derives the forecast or simulation — it's a
presentation layer over pre-computed model output, same as a real BI setup
sitting downstream of a scheduled model-training pipeline.

## Data model

Star schema: one fact table per notebook output, two shared dimension tables.

**Dimension tables** (built in Power Query, not exported from Python):
- `Dim_Date` — calendar table (`CALENDAR(MIN(Fact_Forecast[ds]), MAX(...))` in
  DAX, or generated in Power Query), needed for any date-intelligence measures
  (MTD, YoY, etc.). Mark as a date table in Model view.
- `Dim_Product` — distinct `store` / `item` pairs, pulled from
  `Fact_Reorder` and used as the single source of truth for slicers so every
  page filters on the same product list.

**Fact tables** (one-to-one with an `outputs/*.csv`):

| Table | Source | Grain | Key columns |
|---|---|---|---|
| `Fact_Forecast` | `outputs/forecast_all_series.csv` | date × store × item | `ds`, `yhat`, `yhat_lower`, `yhat_upper`, `actual`, `store`, `item` |
| `Fact_SafetyStockCurve` | `outputs/safety_stock_curve.csv` | store × item × service_level | `service_level`, `safety_stock`, `store`, `item` |
| `Fact_Reorder` | `outputs/reorder_recommendations.csv` | store × item (snapshot) | `on_hand`, `reorder_point`, `min_level`, `max_level`, `eoq`, `needs_reorder`, `suggested_order_qty` |

Relationships: `Dim_Product[store,item]` (composite key, or a concatenated
`store_item` surrogate key built in Power Query) 1-to-many into each fact
table. `Dim_Date[date]` 1-to-many into `Fact_Forecast[ds]` only (the other two
facts are point-in-time snapshots, not date-indexed).

## Pages

**1. Forecast Accuracy**
- Line chart: `actual` vs `yhat` with `yhat_lower`/`yhat_upper` as a shaded
  band, sliced by `Dim_Product`. This is the "does the tuned model actually
  track reality" page.
- KPI tiles: MAPE / MAE computed as DAX measures over the historical (actual
  non-blank) portion of `Fact_Forecast`.
- Product slicer + date range slicer.

**2. Inventory Risk**
- Line/area chart: safety stock vs. service level from `Fact_SafetyStockCurve`,
  with a service-level slicer (values 0.80–0.99) — this is the interactive
  version of the notebook 03 tradeoff chart.
- Scatter: safety stock vs. historical demand variability (sanity-check chart
  from notebook 03), to make the "riskier SKUs get more buffer" story visible.

**3. Reorder Queue**
- Table/matrix from `Fact_Reorder` filtered to `needs_reorder = TRUE`, sorted
  by `suggested_order_qty` descending — the actionable "what do I order today"
  view.
- Bar chart: on-hand vs. min/max levels for the current product selection
  (the notebook 04 chart, made interactive).
- Card tiles: count of SKUs needing reorder, total suggested order quantity.

## Building it

1. Run notebooks 01→04 to populate `outputs/`.
2. Power BI Desktop → Get Data → Text/CSV → point at each `outputs/*.csv`.
3. Build `Dim_Date` and `Dim_Product` in Power Query (see above), wire up
   relationships in Model view.
4. Build the three pages above.
5. Publish to the Power BI service and drop the shareable link + a few
   screenshots/a short GIF walkthrough here in `powerbi/` for the GitHub repo
   (the `.pbix` itself doesn't render on GitHub, so screenshots are what a
   visitor actually sees without opening Power BI Desktop).

## Refresh story ("auto" in "auto min/max")

In a real deployment, notebooks 02–04 would run on a schedule (e.g. nightly),
overwriting `outputs/*.csv`, and the `.pbix` would point at those paths with
a scheduled refresh (Power BI service, or a gateway if the files sit on a
local machine rather than cloud storage) — the Reorder Queue page updates
itself as new forecasts land, which is the actual point of "auto" min/max
versus a static, manually-set policy.
