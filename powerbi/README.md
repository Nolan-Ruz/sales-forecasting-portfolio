# Power BI Dashboard

The presentation layer for the forecasting/inventory pipeline: three pages that turn
the model output in `outputs/` into an accuracy check, a risk view, and an actionable
reorder list. Power BI doesn't re-derive anything here — all forecasting, simulation,
and reorder-logic calculations happen upstream in the notebooks; the dashboard reads
and visualizes their results.

## Pages

**1. Forecast Accuracy** — does the tuned Prophet model actually track real demand?
A line chart plots actual sales against the forecast, with the forecast's uncertainty
range shown as a shaded band, filterable by site, product, and date range. Three KPI
tiles summarize accuracy at a glance: **MAE** and **MAPE** (average forecast error
against known history), and the **percentage of actuals that fell inside the
forecast's uncertainty interval** — a check that the model's confidence bands are
honest, not just that the point forecast is close.

**2. Inventory Risk** — what does it cost to protect against demand uncertainty?
A tradeoff curve shows how much safety stock is required as the target service level
(fill rate) increases from 80% to 99% — the classic cost-of-certainty curve inventory
planners use to set policy. A companion scatter plot checks that the safety-stock
recommendations make sense: SKUs with more historically volatile demand should need
proportionally more buffer stock, and the chart confirms that relationship holds
across all 500 store/item combinations.

**3. Reorder Queue** — what needs to be ordered right now? A sortable table lists
every SKU currently below its reorder point, ranked by suggested order quantity, next
to a chart comparing current on-hand inventory against each SKU's min/max reorder
thresholds. Headline tiles show the total count of at-risk SKUs and the total
recommended order quantity across all of them — the two numbers a replenishment
planner would actually check first.

## Data model

Star schema: one fact table per pipeline stage, with site and product modeled as two
independent dimensions (rather than one combined dimension) so any page can filter by
site or product on its own.

| Table | Grain | What it holds |
|---|---|---|
| `Fact_Forecast` | date × store × item | Prophet's forecast, uncertainty bounds, and actuals where known |
| `Fact_SafetyStockCurve` | store × item × service level | Safety stock required at each target service level |
| `Fact_Inventory_Sim` | store × item | Point-estimate safety stock and expected lead-time demand |
| `Fact_Reorder` | store × item | Reorder point, min/max levels, and order recommendations |
| `Historic_Variability` | store × item | Historical demand variability (coefficient of variation) per SKU |
| `Dim_Site`, `Dim_Product`, `Date` | — | Shared dimensions for slicing and date intelligence |

## Why a `.pbip` instead of a `.pbix`

The project is committed as a **Power BI Project**, which stores the semantic model
(tables, relationships, DAX measures) and report layout as plain text rather than a
single binary file. That means the data model and measures are readable directly on
GitHub, and changes to the dashboard show up as real diffs instead of an opaque blob.

## The "auto" in auto min/max

In a live deployment, the forecasting and inventory notebooks would run on a nightly
schedule, refreshing `outputs/` with the latest forecasts and reorder recommendations,
and the dashboard would pick up the change automatically on its next scheduled
refresh — the Reorder Queue updates itself as new demand data arrives, rather than
relying on someone manually recalculating reorder points.
