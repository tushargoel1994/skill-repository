# Archived operations

These three script/schema pairs were retired on 2026-07-16 after a redundancy review found them substantially duplicated by other live operations. Kept here for reference/backup only — **not maintained, and not referenced by `skill.md` or any live script.**

- `supplier_landed_cost.py` / `.schema.json` — superseded by `supplier_scorecard.py` (operation 7), which now accepts `--startdate`/`--enddate` and exports the same spend-weighted `avg_unit_price`/`total_actual_cost_per_unit` formulas this script used to export as `weighted_avg_unit_price`/`total_actual_cost_per_unit`.
- `supplier_price_trend_by_component.py` / `.schema.json` and `supplier_price_trend_by_criticality.py` / `.schema.json` — merged into `supplier_price_trend.py` (operation 11), which facets by `component_category` when `--component` is omitted, or by `component_criticality` when `--component` is given.
