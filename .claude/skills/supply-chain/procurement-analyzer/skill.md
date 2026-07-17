
---
name: procurement-analyzer  
description: Given procurement order-line data (one row per PO/line item), use this skill to analyze supplier performance and component/category-level procurement trends — pricing, volume, delivery reliability, defect rates, spend concentration, and supplier-vs-peer comparisons. Supports both component-first analysis (a specific component, sliced by supplier/criticality) and supplier-first analysis (a specific supplier, sliced by component/criticality/project/date range).
---

# Procurement analysis (component-first and supplier-first)

This skill analyzes order-line procurement data two ways:

- **Component-first** — start from a component, optionally narrow to a supplier or criticality tier.
- **Supplier-first** — start from a supplier, optionally narrow to a component, criticality tier, project, or date range.

Which mode to use depends entirely on what the operation requires — see [Operations by input requirement](#operations-by-input-requirement) below. It groups all 12 operations by exactly what `--component`/`--supplier`/`--criticality` combination each one needs, so you can pick the right script without reading every description.

## Inputs

Before running any script, confirm:

1. A dataset file that contains procurement data.
2. Whichever of `--component` / `--supplier` / `--criticality` the chosen operation requires — see the operation's own "Requires" line. There is no single rule that covers all 12 scripts; the requirement varies by operation.

A few notes on getting the input right:

- If the dataset or its filepath is missing, ask for it.
- If a component/supplier/criticality/project name given isn't present in the dataset, ask for it — each script exits with a clear error listing the available values when a filter doesn't match, so you don't need to pre-validate by hand.
- For a dataset you haven't analyzed before in this conversation, proactively list the available `component_category` and `component_criticality` values up front (e.g. a quick `df['component_category'].unique()` / `df['component_criticality'].unique()` check) before running any script below, rather than waiting for a script's validation error to surface them. This lets you confirm scope with the user before a run fails.
- The scripts expect the dataset to be a CSV file. Convert whatever the user provides into CSV before running any script.

## Expected Data Schema

The scripts below expect the following columns. If a name differs, rename it in the CSV file before proceeding.

| Column | Required? | Description |
|---|---|---|
| `order_id` | Required | Unique identity of order or invoice |
| `order_date` | Required | Date of order |
| `supplier_name` | Required | Supplier or vendor who fulfilled that order |
| `component_category` | Required | The component; in some datasets mentioned as product, line item, SKU, etc. |
| `component_criticality` | Required | A further subcategorization of component, or simply a variant of the product |
| `unit_cost_usd` | Required | Cost of one unit |
| `qty_ordered` | Optional | Quantity **ordered** — usually present; defaults to 1 unit per row when missing. **Note:** the dataset has no "quantity received" field — every per-unit cost/price calculation in this skill assumes `qty_ordered` ≈ quantity actually delivered. If partial shipments or short-shipments are common in the source data, per-unit figures may be skewed; there's no way to detect or correct for this from the schema alone. |
| `request_date` | Mostly Optional | Date at which buyer wants the product |
| `commit_date` | Mostly Optional | Supplier promised date |
| `received_date` | Optional | Date on which supplies/component were actually received |
| `is_late_arrived` | Optional | Computed automatically when missing: `True` if `received_date > commit_date + grace period` (default 5 days; needs `request_date`/`commit_date` and `received_date` present) |
| `is_open_late` | Optional | A disclosure from buyer that it checked the order later than `received_date` |
| `days_late` | Optional | Computed automatically when missing: `received_date - commit_date` (needs `commit_date` and `received_date` present) |
| `has_md_event` | Optional | Whether a manufacturing defect (or any defect) is present on the order |
| `md_fault_type` | Optional | Type of defect |
| `is_supplier_fault` | Optional | Flag for whether it's the supplier's fault; when missing, defaults to `True` whenever `has_md_event` is `True` |
| `cost_of_rework_usd` | Optional | Amount supplier spent to correct its mistake |
| `days_lost_to_md` | Optional | Days lost due to the manufacturing defect |
| `project_number` | Optional | Project identification the invoice/order belongs to |
| `quarter` | Optional | Quarter in which this transaction took place |
| `line_spend_usd` | Optional | Total expense on that component in that order; computed automatically as `qty_ordered * unit_cost_usd` when missing |

All scripts validate the Required columns above up front and exit with a clear message listing what's missing rather than failing with a raw error. Optional columns are auto-derived or defaulted when absent or blank — see `scripts/commons.py`.

## Before running any operation

- **Always pass explicit, filter-qualified `--output`/`--json-output`/`--image-output` filenames** (e.g. `supplier_scorecard_supplier-BadlandsComponentsLLC.json`, `price_volume_scatter_component-Electrical.png`) rather than relying on the defaults shown below. Every script defaults to the same fixed filename regardless of which component/supplier/criticality was used, so two runs in the same working directory will silently overwrite each other's output otherwise.

- **Before calling a script for the first time in a session, read its schema file** in `schemas/` (referenced under each operation below) to know the exact shape of its JSON output — field names, types, and which fields are conditional on which filters — rather than inferring it from a single sample run. Each is a standalone JSON Schema (draft 2020-12) document.

## Operations by input requirement

Four distinct requirement patterns exist across the 12 operations. Find your pattern first, then the specific operation within it.

**A — `--component` required** (supplier/criticality optional narrowing)

Operations 1–5. These will not run without `--component`. `--supplier` and/or `--criticality` can optionally be added on top to narrow the same component's data further (e.g. "Lakewood Electro Systems in the Critical tier of Optical").

**B — `--component` OR `--supplier` required** (either satisfies it, never neither)

Operations 6–7. Give either one.
- Passing only `--component` analyzes that component across every supplier.
- Passing only `--supplier` (no `--component`) analyzes that supplier across every component they touch, breaking results down by `component_category`.
- `--criticality` alone never satisfies the requirement — it can only narrow further once `--component` or `--supplier` is present.

**C — `--supplier` required** (component/criticality/project/date optional narrowing)

Operations 8–11. `--component` here is *only* a narrowing filter, never a substitute for `--supplier` — unlike group B, omitting `--component` does not change which script you're allowed to run, it just widens the scope to every component the supplier touches.

> **Exception:** operation 11 (Supplier Price Trend vs. Peers) breaks this group's general rule — its optional `--component` doesn't just narrow scope, it switches which dimension the chart facets by (component category vs. criticality tier within one component). See its own write-up below; don't assume `--component` is "just a filter" there the way it is for every other Group C operation.

**D — `--supplier` required, no `--component` argument exists at all**

Operation 12. Structurally similar to group C but stricter: this one script has no `--component` flag whatsoever, so it always covers the supplier's full component portfolio.

---

## Operations at a Glance

| # | Operation | Required inputs | Optional inputs | Outputs | Script | Brief | Schema |
|---|---|---|---|---|---|---|---|
| 1 | Component Summary | `--component` | `--supplier`, `--criticality` | JSON | `component_summary.py` | Basic procurement stats (spend, quantity, PO count, suppliers, projects, on-time %, defect rate, rework cost) for the filtered scope. | `component_summary.schema.json` |
| 2 | Sub Category Level Supplier Division | `--component` | `--supplier`, `--criticality` | PNG + JSON | `criticality_supplier_heatmap.py` | Classifies each supplier as strategic/major/smaller by criticality-tier spend share, with a supplier × criticality heatmap. | `criticality_supplier_heatmap.schema.json` |
| 3 | Supplier Relationship (Price vs. Volume) | `--component` | `--supplier`, `--criticality` | PNG + JSON | `price_volume_scatter.py` | Categorizes suppliers by price charged (Cheaper/Acceptable/Expensive) and volume contributed (Low/Healthy/Strategic). | `price_volume_scatter.schema.json` |
| 4 | Purchase Trends | `--component` | `--supplier`, `--criticality` | PNG + JSON | `price_volume_trend.py` | Monthly average unit price and volume purchased over time for the filtered scope. | `price_volume_trend.schema.json` |
| 5 | Defect Root-Cause and Schedule Impact | `--component` | `--supplier`, `--criticality` | PNG + JSON | `defect_root_cause_analysis.py` | Breaks defect events down by fault type, supplier schedule impact, and project. | `defect_root_cause_analysis.schema.json` |
| 6 | Request Commit Received Gaps | `--component` OR `--supplier` | `--criticality` | JSON | `request_commit_actual_gap.py` | Splits POs into on-time-as-requested / committed-later / delayed-beyond-commit, with day-gap stats. | `request_commit_actual_gap.schema.json` |
| 7 | Supplier Ranking and Scorecard | `--component` OR `--supplier` | `--criticality`, `--startdate`, `--enddate` | JSON | `supplier_scorecard.py` | Core performance scorecard: spend share, pricing, delivery reliability, defect rate/attribution, rework economics. | `supplier_scorecard.schema.json` |
| 8 | Supplier Summary | `--supplier` | `--component`, `--criticality` | JSON | `supplier_summary.py` | Supplier-first orientation: headline stats, per-component breakdown, defect fault-type Pareto, open late orders. | `supplier_summary.schema.json` |
| 9 | Supplier Component/Criticality Share Breakdown | `--supplier` | `--component`, `--project` | 2× PNG + JSON | `supplier_share_breakdown.py` | This supplier's qty/spend/PO share of each component and criticality tier vs. the peer set, plus delay burden. | `supplier_share_breakdown.schema.json` |
| 10 | Supplier Project/Component Matrix | `--supplier` | `--component`, `--project` | PNG + JSON | `supplier_project_component_matrix.py` | How a supplier's spend on a project breaks down by component. | `supplier_project_component_matrix.schema.json` |
| 11 | Supplier Price Trend vs. Peers | `--supplier` | `--component` (switches facet dimension — see caveat above) | PNG + JSON | `supplier_price_trend.py` | Supplier's monthly avg unit price vs. all other suppliers, faceted by component (whole portfolio) or by criticality tier (if `--component` given). | `supplier_price_trend.schema.json` |
| 12 | Supplier Defect Heatmap by Quarter | `--supplier` (no `--component` flag exists) | — | PNG + JSON | `supplier_defect_heatmap.py` | MD (defect) rate by component × quarter for the supplier — is a quality problem concentrated in specific components/periods? | `supplier_defect_heatmap.schema.json` |

---

## Group A — Component required

### 1. Component Summary

- **Requires:** `--component`
- **Optional:** `--supplier`, `--criticality`

Basic procurement statistics for the filtered scope, printed and exported as JSON. Use this first for a quick orientation before running anything heavier. Covers:

- Spend, quantity ordered, PO count
- Active suppliers, projects touched
- On-time delivery %, defect rate
- Rework cost, open-late PO count

**Execute:**
```
scripts/component_summary.py --filepath [filename in .csv] --component [component name] [--supplier [name]] [--criticality [name]] --output [filename]
```

**Output:** JSON — `schemas/component_summary.schema.json`. `component_breakdown` is the whole-scope summary (single-element array); `criticality_breakdown` is the same stats split by `component_criticality` tier.

### 2. Sub Category Level Supplier Division

- **Requires:** `--component`
- **Optional:** `--supplier`, `--criticality`

Classifies each supplier of the component by criticality-tier spend share, with a heatmap of supplier × criticality spend. Use when the user wants to know which suppliers dominate which criticality tier of a component.

- **Strategic** — ≥25% of a criticality tier's spend
- **Major** — ≥10–25%
- **Smaller** — below 10%

> **Caveat:** the strategic/major threshold has no minimum sample-size floor — a supplier can cross it off a single PO if that criticality tier's total spend is small. Before treating a "major"/"strategic" label as meaningful, cross-check that supplier's `po_count`/`n_projects` via Supplier Ranking and Scorecard (operation 7); a label backed by one PO is a different signal than one backed by dozens.

**Execute:**
```
scripts/criticality_supplier_heatmap.py --filepath [filename in .csv] --component [component name] [--supplier [name]] [--criticality [name]] --image-output [filename] --json-output [filename]
```

**Output:** PNG + JSON — `schemas/criticality_supplier_heatmap.schema.json`. `component_breakdown` (spend per supplier, all tiers combined) and `criticality_breakdown` (spend/share per supplier × criticality tier, long form) are the tabular data underlying both the heatmap image and `segments`. `qualifying_tiers` on each flagged supplier in `segments` lists every criticality tier where they crossed the threshold, richest share first — this answers "which tier is this supplier actually major in" without recomputing the share matrix by hand.

### 3. Supplier Relationship (Price vs. Volume)

- **Requires:** `--component`
- **Optional:** `--supplier`, `--criticality`

Categorizes every supplier of the component along two axes. Feeds the "Reduce Number of Suppliers" and "Replace vs Negotiate vs Keep" playbooks below.

- **Price charged** (percentile-based): Cheaper / Acceptable / Expensive
- **Volume contributed:** Low / Healthy / Strategic

> **Note:** `avg_price` is spend-weighted (`total_spend / total_qty`), not a plain mean of `unit_cost_usd`, so PO-size variance doesn't distort `price_category`.

**Execute:**
```
scripts/price_volume_scatter.py --filepath [filename in .csv] --component [component name] [--supplier [name]] [--criticality [name]] --image-output [filename] --json-output [filename]
```

**Output:** PNG + JSON — `schemas/price_volume_scatter.schema.json`. `component_breakdown` (per supplier — what the chart plots) and `criticality_breakdown` (per supplier × criticality tier) are computed independently, so percentile/volume-share values aren't comparable across the two arrays.

### 4. Purchase Trends

- **Requires:** `--component`
- **Optional:** `--supplier`, `--criticality`

Monthly average unit price (line) and volume purchased (bars) over time for the filtered scope. Use for "how has pricing/volume moved over time" questions.

> **Note:** `avg_unit_price` here is intentionally an unweighted mean of `unit_cost_usd` per month — a defensible, common choice for a trend line (equal weight per transaction reveals quoted-price movement over time; spend-weighting would answer a different question and could mask price creep behind a few large low-priced orders).

**Execute:**
```
scripts/price_volume_trend.py --filepath [filename in .csv] --component [component name] [--supplier [name]] [--criticality [name]] --output [filename] --json-output [filename]
```

**Output:** PNG + JSON — `schemas/price_volume_trend.schema.json`. `component_breakdown` (per month) and `criticality_breakdown` (per month × criticality tier) mirror what the chart plots, plus the criticality split.

### 5. Defect Root-Cause and Schedule Impact

- **Requires:** `--component`
- **Optional:** `--supplier`, `--criticality`

Breaks defect events down by fault type (Pareto), by supplier (schedule days lost, fault attribution), and by project. Use when the user wants to know *why* defects are happening and *how much schedule time* they cost — not just the defect rate a scorecard already gives.

- Requires `has_md_event` present and at least one of `md_fault_type`/`days_lost_to_md` populated
- Exits with a clear message if that data isn't available

**Execute:**
```
scripts/defect_root_cause_analysis.py --filepath [filename in .csv] --component [component name] [--supplier [name]] [--criticality [name]] --image-output [filename] --json-output [filename]
```

**Output:** PNG + JSON — `schemas/defect_root_cause_analysis.schema.json`. Four arrays: `fault_type_breakdown`, `supplier_schedule_impact`, `supplier_criticality_breakdown` (the same supplier data further split by `component_criticality`), and `project_schedule_impact`. Chart is a two-panel PNG (fault-type Pareto + supplier schedule impact) mirroring `fault_type_breakdown`/`supplier_schedule_impact`.

## Group B — Component OR supplier required (either satisfies it)

### 6. Request Commit Received Gaps

- **Requires:** `--component` OR `--supplier` (never neither; `--criticality` alone is not sufficient)
- **Optional:** `--criticality`

Splits POs into three buckets, with count/avg/std/min/max day-gap stats for the latter two:

- On-time as requested
- Committed later
- Delayed beyond commit

Requires `request_date`, `commit_date`, and `received_date` present — ask for these (or a substitute dataset) if the script reports them missing.

**Execute:**
```
scripts/request_commit_actual_gap.py --filepath [filename in .csv] [--component [component name] | --supplier [supplier name]] [--criticality [name]] --output [filename]
```

**Output:** JSON — `schemas/request_commit_actual_gap.schema.json`. `component_breakdown` is a single row (whole component) when `--component` was given, or one row per `component_category` when only `--supplier` was given. `criticality_breakdown` adds `component_criticality` as an extra groupby key on top. Gap-stat sub-objects are flattened into prefixed columns (`committed_later_avg_days`, etc.) rather than nested.

### 7. Supplier Ranking and Scorecard

- **Requires:** `--component` OR `--supplier` (never neither)
- **Optional:** `--criticality`, `--startdate`/`--enddate`

The core performance scorecard — one row per supplier of the component, or (given `--supplier` instead) one row per component the supplier touches. This is the primary input to the "Replace vs Negotiate vs Keep" table below. Covers:

- Spend share
- Pricing
- Delivery reliability
- Defect rate/attribution
- Rework economics

> **Note:** `avg_unit_price` and `total_actual_cost_per_unit` are both spend-weighted (`total_spend / total_qty` and `(total_spend + rework_cost) / total_qty` respectively) — consistent with each other.

> **`--startdate`/`--enddate`** (both optional, independent, inclusive, `YYYY-MM-DD`) narrow the scope to an order-date range — usable on any run (component-only, supplier-only, or both), not just supplier-scoped runs. This subsumes the former Supplier Landed Cost operation's only unique capability; Supplier Landed Cost has been retired and archived (see `_archive/`) now that `avg_unit_price`/`total_actual_cost_per_unit` here are the same spend-weighted formulas it used to export as `weighted_avg_unit_price`/`total_actual_cost_per_unit`.

**Execute:**
```
scripts/supplier_scorecard.py --filepath [filename in .csv] [--component [component name] | --supplier [supplier name]] [--criticality [name]] [--startdate YYYY-MM-DD] [--enddate YYYY-MM-DD] --output [filename]
```

**Output:** JSON — `schemas/supplier_scorecard.schema.json`. `component_breakdown` is the primary breakdown (per supplier, or per component when `--component` is omitted — same data previously exported under the key `suppliers`); `criticality_breakdown` adds `component_criticality` as an extra groupby key. `filters` also includes `start_date`/`end_date` (both `null` when not passed).

## Group C — Supplier required (component optional narrowing, plus a script-specific extra filter)

### 8. Supplier Summary

- **Requires:** `--supplier`
- **Optional:** `--component`, `--criticality`

The supplier-first analogue of Component Summary. Use this first for a quick orientation on one supplier, the same way Component Summary orients on one component. Includes:

- Headline stats: spend, PO count, components served, first/last PO, OTD%, defect rate, rework cost, days lost to MD, open-late count
- A per-component breakdown: spend/pricing/delivery/quality plus share-of-category-spend and price-index-vs-peers
- A defect fault-type Pareto and supplier-fault attribution
- Any open late orders

> **Note:** `avg_unit_price` and the internal peer average feeding `price_index_vs_peers_pct` are both spend-weighted (`total_spend / total_qty`), not plain means of `unit_cost_usd`.

**Execute:**
```
scripts/supplier_summary.py --filepath [filename in .csv] --supplier [supplier name] [--component [name]] [--criticality [name]] --output [filename]
```

**Output:** JSON — `schemas/supplier_summary.schema.json`.

### 9. Supplier Component/Criticality Share Breakdown

- **Requires:** `--supplier`
- **Optional:** `--component`, `--project` (unique to this operation — not a filter any other script accepts)

How much of a component's (and each criticality tier's) qty/spend/PO business this supplier actually holds, plus delay burden and delayed %, versus the peer set in the same scope.

- Dominant if ≥25% of spend (same threshold as the "Replace vs Negotiate vs Keep" table)
- Peer comparisons are computed within whatever `--component`/`--project` scope is given, not the whole dataset — narrowing to one project can show a very different picture than the component-wide view (a supplier with modest overall share can be dominant within a single project)
- Produces exactly 2 charts (quantity share, spend share), both plotting the finer component×criticality rows

**Execute:**
```
scripts/supplier_share_breakdown.py --filepath [filename in .csv] --supplier [supplier name] [--component [name]] [--project [project number]] --qty-chart-output [filename] --spend-chart-output [filename] --json-output [filename]
```

**Output:** 2× PNG + JSON — `schemas/supplier_share_breakdown.schema.json`. Full detail at both breakdown levels (`component_breakdown`, `criticality_breakdown`); charts only visualize the share percentages.

### 10. Supplier Project/Component Matrix

- **Requires:** `--supplier`
- **Optional:** `--component`, `--project` (same filter as Supplier Component/Criticality Share Breakdown, operation 9)

How a supplier's spend on a project breaks down by component — e.g. "what is Badlands actually supplying on Project X?" No peer comparison. Use when the user wants to understand a supplier's actual scope of work within one project.

- The heatmap is **component-level only** (project × component_category, spend)
- The JSON goes further, adding a finer project × component × criticality breakdown the chart doesn't visualize

**Execute:**
```
scripts/supplier_project_component_matrix.py --filepath [filename in .csv] --supplier [supplier name] [--component [name]] [--project [project number]] --image-output [filename] --json-output [filename]
```

**Output:** PNG + JSON — `schemas/supplier_project_component_matrix.schema.json`.

### 11. Supplier Price Trend vs. Peers

- **Requires:** `--supplier`
- **Optional:** `--component` — unlike every other Group C operation, this does not just narrow scope: it **switches which dimension the chart facets by**.

One small-multiples chart, one subplot per facet value the supplier actually has orders in, each plotting the supplier's monthly average unit price against every other supplier of that same facet slice. Use for "is this supplier's pricing moving in line with the market" questions — either across their whole portfolio, or narrowed to one component's criticality tiers when a specific component is already in question.

- Omit `--component` to facet by `component_category` across the supplier's whole portfolio (all criticality tiers combined)
- Give `--component` to scope to that one component and facet by `component_criticality` instead; exits with a clear message if the supplier has no orders in the given component at all

**Execute:**
```
scripts/supplier_price_trend.py --filepath [filename in .csv] --supplier [supplier name] [--component [component name]] --image-output [filename] --json-output [filename]
```

**Output:** PNG + JSON — `schemas/supplier_price_trend.schema.json`. Exactly one of `by_component` (no `--component` given) / `by_criticality` (`--component` given) is populated per run, never both. Each has one dynamic key per facet value, with `target_po_count`/`peer_po_count` (sanity-check the comparison isn't based on too few peer orders) plus the two monthly price series.

## Group D — Supplier required, no `--component` argument exists

### 12. Supplier Defect Heatmap by Quarter

- **Requires:** `--supplier` only — no `--component` flag exists on this script

MD (defect) rate by component × quarter for the supplier — use when the user wants to know whether a supplier's quality problem is concentrated in specific components, specific time periods, or both (e.g. "is Badlands' quality problem getting worse, or has it always been like this?").

- Quarters are sorted chronologically (by parsed year and quarter number, not lexically as strings), so the heatmap's time axis reads correctly left-to-right
- Exits with a clear message if no defect data (`has_md_event`) is tracked for the supplier at all, rather than silently rendering an all-0% heatmap that would be indistinguishable from genuinely zero defects (same check as Defect Root-Cause and Schedule Impact, operation 5)
- No criticality split — analysis stays component-level

**Execute:**
```
scripts/supplier_defect_heatmap.py --filepath [filename in .csv] --supplier [supplier name] --image-output [filename] --json-output [filename]
```

**Output:** PNG + JSON — `schemas/supplier_defect_heatmap.schema.json`. `component_quarter_defect_rate` mirrors exactly what the heatmap visualizes, plus `po_count`/`defect_count` so a rate computed from a tiny sample isn't over-trusted.

---

## Key Procurement operations

### Reduce Number of Suppliers or consolidate supplier base

Look at Supplier Relationship (Price vs. Volume, operation 3) to find expensive and low-volume suppliers, then check with Sub Category Level Supplier Division (operation 2) to ensure the supplier is not a major supplier for any subcategory, and finish with Supplier Ranking and Scorecard (operation 7) to identify the top suppliers that should be considered for exit.

The key is that high volume contribution suppliers are difficult to remove, and hence negotiations or pressure tactics are the better route. Use your procurement knowledge for suggestions.

### Replace vs Negotiate vs Keep

> **Caveat: only valid when a specific `--component` was used.** `volume_category` (from operation 3) and `pct_spend_contribution` (from operation 7) are both computed relative to that component's totals — a cross-component (supplier-only) or criticality-only run's percentages aren't comparable across components, so don't apply this table to that kind of output.

Combine Supplier Relationship (Price vs. Volume, operation 3)'s `volume_category`, Supplier Ranking and Scorecard (operation 7)'s `pct_spend_contribution`, and delivery/quality performance to decide a supplier's fate:

- **Poor performance** = any of: `otd_pct < 85`, `avg_days_late > 5` (the same grace period `commons.py` uses to compute `is_late_arrived`), `md_rate_pct_supplier_error > 10`, `rework_cost_pct_of_spend > 3`.
- **Top spend concentrator** = `pct_spend_contribution >= 10` — a supplier can be Low/Healthy Volume by unit count but still dominate spend (e.g. due to high unit price), which `volume_category` alone would miss.

| Volume category | Spend concentration | Performance | Recommended action |
|---|---|---|---|
| Low Volume | Not a top concentrator (`pct_spend_contribution < 10%`) | Poor | **Replace** |
| Low Volume | Top concentrator (`pct_spend_contribution >= 10%`) | Poor | **Negotiate** |
| Healthy Volume or Strategic Supplier | any | Poor | **Negotiate** |
| any (Low / Healthy / Strategic) | any | Clean (none of the poor-performance thresholds breached) | **Keep** |

Suppliers landing in "Replace" are strong exit candidates — low leverage, low switching cost, and a track record of problems. "Negotiate" suppliers have leverage (either volume or spend concentration) that makes outright replacement costly, so use price/SLA renegotiation or performance-improvement plans instead. "Keep" suppliers have no material delay/defect issues regardless of tier and don't need intervention.

### Procurement Strategy

- **Pricing and Volume:** check if the procurement is efficient in terms that more purchase happens at low prices (Supplier Relationship (Price vs. Volume), operation 3).
- **Receive Gap Analysis + Supplier Scorecard:** use this to know if any particular subcategory or supplier is delaying the project and strategy needs to be evaluated there (Request Commit Received Gaps, operation 6, and Supplier Ranking and Scorecard, operation 7).
- **Defect Root-Cause + Schedule Impact:** when Supplier Ranking and Scorecard (operation 7) flags a high defect rate, use Defect Root-Cause and Schedule Impact (operation 5) to see which fault types are recurring and which suppliers/projects are losing the most schedule days to them — this distinguishes a supplier worth replacing on quality economics from one with a merely high defect *rate* but low actual cost/schedule impact.
- **Supplier-first deep dive:** for a single supplier already flagged as a concern —
  1. Supplier Summary (operation 8) gives the fastest orientation.
  2. Supplier Ranking and Scorecard (operation 7), narrowed with `--startdate`/`--enddate` to the concern window, gives the true cost over that period.
  3. Supplier Price Trend vs. Peers (operation 11) gives the pricing trajectory.
  4. Supplier Defect Heatmap by Quarter (operation 12) gives defect timing/concentration.
