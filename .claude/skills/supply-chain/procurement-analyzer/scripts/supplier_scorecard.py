import argparse
import json
import sys
from pathlib import Path

import pandas as pd
import commons

# One orthogonal signal per scoring dimension (weight, cost, delivery
# frequency/severity, quality frequency/attribution/cost) — the rest of the
# scorecard's columns are diagnostic detail or duplicated by other exports
# (price/volume share, request-commit gap analysis, etc.). avg_unit_price is
# included alongside total_actual_cost_per_unit so this JSON export alone
# covers what the retired supplier_landed_cost.py used to export as
# weighted_avg_unit_price/total_actual_cost_per_unit.
SCORECARD_JSON_FIELDS = [
    "pct_spend_contribution",
    "avg_unit_price",
    "total_actual_cost_per_unit",
    "otd_pct",
    "avg_days_late",
    "md_rate_pct",
    "md_rate_pct_supplier_error",
    "rework_cost_pct_of_spend",
]


def build_supplier_scorecard(d: pd.DataFrame, group_keys: list) -> pd.DataFrame:
    """Composite supplier scorecard: pricing, spend/volume share, delivery
    reliability & severity, quality, rework economics, and portfolio
    concentration. `group_keys` is ["supplier_name"] for a single-component
    run, or ["component_category"] for a cross-component run scoped to one
    supplier (the supplier is already fixed by the caller's filter in that case)."""
    total_spend_all = d["line_spend_usd"].sum()
    total_qty_all = d["qty_ordered"].sum()
    if "request_date" in d.columns and "commit_date" in d.columns:
        request_commit_gap = (d["commit_date"] - d["request_date"]).dt.days
    else:
        request_commit_gap = pd.Series(float("nan"), index=d.index)

    scorecard = d.groupby(group_keys).agg(
        po_count=("order_id", "count"),
        total_spend=("line_spend_usd", "sum"),
        total_qty=("qty_ordered", "sum"),
        std_unit_price=("unit_cost_usd", "std"),
        otd_pct=("is_late_arrived", lambda x: (1 - x.fillna(False).mean()) * 100),
        avg_days_late=("days_late", "mean"),
        std_days_late=("days_late", "std"),
        md_rate_pct=("has_md_event", lambda x: x.fillna(False).mean() * 100),
        md_rate_pct_supplier_error=("is_supplier_fault", lambda x: x.fillna(False).mean() * 100),
        rework_cost=("cost_of_rework_usd", "sum"),
        n_projects=("project_number", "nunique"),
        n_quarters=("quarter", "nunique"),
        open_late_count=("is_open_late", lambda x: int((x == True).sum())),
    )

    scorecard["avg_request_commit_gap_days"] = request_commit_gap.groupby([d[k] for k in group_keys]).mean()

    open_late = d[d["is_open_late"] == True]
    scorecard["open_late_max_days_late"] = (
        open_late.groupby(group_keys)["days_late"].max()
        .reindex(scorecard.index).fillna(0)
    )

    scorecard["avg_unit_price"] = scorecard["total_spend"] / scorecard["total_qty"]
    scorecard["std_unit_price"] = scorecard["std_unit_price"].fillna(0)
    scorecard["std_days_late"] = scorecard["std_days_late"].fillna(0)
    scorecard["avg_po_size"] = scorecard["total_spend"] / scorecard["po_count"]
    scorecard["rework_cost_pct_of_spend"] = scorecard["rework_cost"] / scorecard["total_spend"] * 100
    scorecard["total_actual_cost_per_unit"] = (
        (scorecard["total_spend"] + scorecard["rework_cost"]) / scorecard["total_qty"]
    )
    scorecard["pct_volume_contribution"] = scorecard["total_qty"] / total_qty_all * 100
    scorecard["pct_spend_contribution"] = scorecard["total_spend"] / total_spend_all * 100

    return scorecard[[
        "po_count", "total_spend", "total_qty", "avg_po_size",
        "pct_spend_contribution", "pct_volume_contribution",
        "avg_unit_price", "std_unit_price", "total_actual_cost_per_unit",
        "otd_pct", "avg_days_late", "std_days_late",
        "open_late_count", "open_late_max_days_late",
        "avg_request_commit_gap_days",
        "md_rate_pct", "md_rate_pct_supplier_error",
        "rework_cost", "rework_cost_pct_of_spend",
        "n_projects", "n_quarters",
    ]].round(2).sort_values("total_spend", ascending=False)


def print_supplier_scorecard(scorecard: pd.DataFrame, label: str) -> None:
    print(f"\nSupplier Scorecard — {label}")
    print("-" * 100)
    print(scorecard.to_string())
    print()


def export_scorecard_json(component_breakdown: pd.DataFrame, criticality_breakdown: pd.DataFrame,
                           filters: dict, output_path: str = "supplier_scorecard.json") -> str:
    """Write only the scoring-relevant fields (SCORECARD_JSON_FIELDS) to JSON,
    plus whichever group_keys columns reset_index() expands back out."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "filters": filters,
        "component_breakdown": component_breakdown[SCORECARD_JSON_FIELDS].reset_index().to_dict(orient="records"),
        "criticality_breakdown": criticality_breakdown[SCORECARD_JSON_FIELDS].reset_index().to_dict(orient="records"),
    }
    path.write_text(json.dumps(payload, indent=2))
    return str(path)


def main(file_path, component_name=None, supplier_name=None, criticality_name=None,
         start_date=None, end_date=None,
         output_path="supplier_scorecard.json") -> None:
    """Read the file, print the full supplier scorecard, and export the
    trimmed scoring-relevant fields as JSON. Requires --component or
    --supplier (never neither); when --component is omitted, results are
    broken down by component_category for the given supplier. Optional
    --startdate/--enddate narrow to an order_date range (inclusive), usable
    regardless of whether --component and/or --supplier is set — this also
    covers what the retired supplier_landed_cost.py used to provide, since
    total_actual_cost_per_unit/avg_unit_price here are the same spend-weighted
    formulas it exported as total_actual_cost_per_unit/weighted_avg_unit_price."""
    df = commons.load_dataset(file_path)
    commons.require_component_or_supplier(component_name, supplier_name, context="supplier_scorecard")
    commons.validate_filters(df, component=component_name, supplier=supplier_name, criticality=criticality_name)
    d = commons.filter_dataset(df, component=component_name, supplier=supplier_name, criticality=criticality_name)
    d = commons.filter_date_range(d, start_date, end_date)
    if d.empty:
        print("No orders found for the given scope/date range.")
        sys.exit(1)
    label = commons.describe_filters(component_name, supplier_name, criticality_name)
    if start_date or end_date:
        label = f"{label} | {start_date or '...'} to {end_date or '...'}"

    if component_name is not None:
        primary_key, fine_keys = "supplier_name", ["supplier_name", "component_criticality"]
    else:
        primary_key, fine_keys = "component_category", ["component_category", "component_criticality"]

    component_breakdown = build_supplier_scorecard(d, [primary_key])
    criticality_breakdown = build_supplier_scorecard(d, fine_keys)
    print_supplier_scorecard(component_breakdown, label)

    filters = commons.filters_dict(component_name, supplier_name, criticality_name)
    filters["start_date"] = start_date
    filters["end_date"] = end_date
    saved_path = export_scorecard_json(component_breakdown, criticality_breakdown, filters, output_path)
    print(f"Supplier scorecard written to: {saved_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--filepath", required=True)
    parser.add_argument("--component", default=None)
    parser.add_argument("--supplier", default=None)
    parser.add_argument("--criticality", default=None)
    parser.add_argument("--startdate", default=None, help="YYYY-MM-DD, inclusive")
    parser.add_argument("--enddate", default=None, help="YYYY-MM-DD, inclusive")
    parser.add_argument("--output", default="supplier_scorecard.json")
    args = parser.parse_args()
    main(args.filepath, args.component, args.supplier, args.criticality,
         args.startdate, args.enddate, args.output)
