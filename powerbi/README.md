# Power BI Dashboard

Built on the CSV/Parquet tables exported by the notebooks into `outputs/`.
Nothing in Power BI re-derives the forecast or simulation — it's a
presentation layer over pre-computed model output, same as a real BI setup
sitting downstream of a scheduled model-training pipeline.

## Data model

Star schema: one fact table per notebook output, three shared dimension
tables. Site and product are modeled as two separate dimensions rather than
one combined `store`/`item` dimension — lets any page slice by site or
product independently instead of only as a pair.

**Dimension tables** (built in Power Query / DAX, not exported from Python):
- `Date` — calendar table (`CALENDAR(MIN(Fact_Forecast[ds]), MAX(...))` in
  DAX), needed for any date-intelligence measures (MTD, YoY, etc.). Marked as
  a date table in Model view.
- `Dim_Site` — distinct `store` values.
- `Dim_Product` — distinct `item` values.

**Fact tables** (one-to-one with an `outputs/*.csv`):

| Table | Source | Grain | Key columns |
|---|---|---|---|
| `Fact_Forecast` | `outputs/forecast_all_series.csv` | date × store × item | `ds`, `yhat`, `yhat_lower`, `yhat_upper`, `actual`, `store`, `item` |
| `Fact_SafetyStockCurve` | `outputs/safety_stock_curve.csv` | store × item × service_level | `service_level`, `safety_stock`, `store`, `item` |
| `Fact_Reorder` | `outputs/reorder_recommendations.csv` | store × item (snapshot) | `on_hand`, `reorder_point`, `min_level`, `max_level`, `eoq`, `needs_reorder`, `suggested_order_qty` |
| `Fact_Inventory_Sim` | `outputs/inventory_simulation.csv` | store × item (point estimate) | `expected_lead_time_demand`, `safety_stock`, `p95_lead_time_demand`, `store`, `item` |
| `Historic_Variablity`¹ | `outputs/series_variability.csv` | store × item | `mean`, `std`, `cv`, `store`, `item` |

¹ Named `Historic_Variablity` in the model (typo — should be
`Historic_Variability`); documented as-built, worth a rename in Power BI
Desktop (Model view → right-click table → Rename) before this goes public.

Relationships: `Dim_Site[store]` (1) → each fact table's `store` column
(many), and `Dim_Product[item]` (1) → each fact table's `item` column (many)
— every fact table gets both relationships. `Date[Date]` (1) →
`Fact_Forecast[ds]` (many) only (the other facts are point-in-time snapshots,
not date-indexed).

## Pages

**1. Forecast Accuracy**
- Line chart: `actual` vs `yhat` with `yhat_lower`/`yhat_upper` as a shaded
  band, sliced by `Dim_Site`/`Dim_Product`. This is the "does the tuned model
  actually track reality" page.
- KPI tiles: MAPE / MAE computed as DAX measures over the historical (actual
  non-blank) portion of `Fact_Forecast`.
- Site slicer + product slicer + date range slicer.

**2. Inventory Risk**
- Line/area chart: safety stock vs. service level from `Fact_SafetyStockCurve`,
  with a service-level slicer (values 0.80–0.99) — this is the interactive
  version of the notebook 03 tradeoff chart.
- Scatter: `Fact_Inventory_Sim[safety_stock]` (y) vs. `Historic_Variablity[cv]`
  (x), with both `Dim_Site[store]` and `Dim_Product[item]` on the Details
  well so each store/item combination renders as its own point — the
  sanity-check chart from notebook 03, made interactive, to make the "riskier
  SKUs get more buffer" story visible.

**3. Reorder Queue**
- Table/matrix from `Fact_Reorder` filtered to `needs_reorder = TRUE`, sorted
  by `suggested_order_qty` descending — the actionable "what do I order today"
  view.
- Line and clustered column chart: `on_hand` as the column, `min_level`/
  `max_level` as zero-stroke-width line series with markers (per-category
  threshold ticks rather than a connected line) — the notebook 04 chart, made
  interactive. Filtered to `needs_reorder = TRUE` and Top N by
  `suggested_order_qty`, since showing all 500 SKUs at once is unreadable.
- Card tiles: `# of Products Needing Reordering` (`COUNTROWS(Fact_Reorder)`
  filtered to `needs_reorder = TRUE`), total suggested order quantity.

## Building it

The model/report live as a **Power BI Project (`.pbip`)** — `sales_forecasting.pbip`
plus the `sales_forecasting.Report/` and `sales_forecasting.SemanticModel/`
folders next to it. Unlike a `.pbix`, these are plain text (TMDL for the
model — tables, measures, relationships; JSON for the report layout), so
diffs are readable in git/GitHub instead of being an opaque binary. The
`.pbi/` subfolder inside each (cache, local settings) is gitignored —
machine-local, regenerated on open, not part of the model.

1. Run notebooks 01→04 to populate `outputs/`.
2. Open `powerbi/sales_forecasting.pbip` in Power BI Desktop (requires the
   "Power BI Project (.pbip) save option" preview feature enabled once:
   File → Options and settings → Options → Preview features).
3. Get Data → Text/CSV → point at each `outputs/*.csv` if adding a new
   source, or Refresh if the tables already exist.
4. Model already has `Date`, `Dim_Site`, `Dim_Product` and the relationships
   described above; extend as needed in Model view.
5. Build/edit the three pages above.
6. Publish to the Power BI service and drop the shareable link + a few
   screenshots/a short GIF walkthrough here in `powerbi/` for the GitHub repo
   (a live report doesn't render on GitHub, so screenshots are what a visitor
   actually sees without opening Power BI Desktop).

## Refresh story ("auto" in "auto min/max")

In a real deployment, notebooks 02–04 would run on a schedule (e.g. nightly),
overwriting `outputs/*.csv`, and the report would point at those paths with
a scheduled refresh (Power BI service, or a gateway if the files sit on a
local machine rather than cloud storage) — the Reorder Queue page updates
itself as new forecasts land, which is the actual point of "auto" min/max
versus a static, manually-set policy.
