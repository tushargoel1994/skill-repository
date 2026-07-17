"""True landed cost for a supplier, corrected from datasets/1-supplier-stability-
dateset-for-procurement/scripts/supplier_report.py's show_landed_cost_table,
which used a plain (unweighted) mean of unit_cost_usd as "average price" —
wrong whenever PO sizes vary, since it treats a 1-unit order and a 500-unit
order as equally representative of the average price paid.

Corrected metrics, computed per group:
  - weighted_avg_unit_price = total_spend / total_qty (spend-weighted, not a
    plain mean of unit_cost_usd — this is the actual average price paid per
    unit across all POs in the group)
  - total_qty            = sum(qty_ordered)
  - total_spend           = sum(line_spend_usd)
  - total_rework_cost     = sum(cost_of_rework_usd)
  - total_cost            = total_spend + total_rework_cost
  - total_actual_cost_per_unit = total_cost / total_qty

Computed at two breakdown levels (both on the target supplier's own data,
no peer comparison): one row per component_category, and one row per
(component_category, component_criticality) combination.

--startdate/--enddate are a filter dimension (order_date range) commons.py
doesn't support, so handled locally here.
"""
import argparse
import json
import sys
from pathlib import Path

import pandas as pd
import commons


def _parse_date(value: str, flag: str) -> pd.Timestamp:
    ts = pd.to_datetime(value, errors="coerce")
    if pd.isna(ts):
        print(f"Could not parse {flag} '{value}' as a date (expected YYYY-MM-DD).")
        sys.exit(1)
    return ts


def compute_landed_cost(d: pd.DataFrame, group_keys: list) -> pd.DataFrame:
    agg = d.groupby(group_keys).agg(
        po_count=("order_id", "count"),
        total_qty=("qty_ordered", "sum"),
        total_spend=("line_spend_usd", "sum"),
        total_rework_cost=("cost_of_rework_usd", "sum"),
    )
    agg["total_cost"] = agg["total_spend"] + agg["total_rework_cost"]
    agg["weighted_avg_unit_price"] = agg["total_spend"] / agg["total_qty"]
    agg["total_actual_cost_per_unit"] = agg["total_cost"] / agg["total_qty"]
    return agg.round(2).sort_values("total_spend", ascending=False)


def print_table(title: str, label: str, rows: list) -> None:
    print(f"\n{title} — {label}")
    print("-" * 110)
    print(pd.DataFrame(rows).to_string(index=False) if rows else "No data.")
    print()


def main(file_path, supplier_name, component_name=None, start_date=None, end_date=None,
         output_path="supplier_landed_cost.json") -> None:
    df = commons.load_dataset(file_path)
    commons.validate_filters(df, component=component_name, supplier=supplier_name)
    target_df = commons.filter_dataset(df, component=component_name, supplier=supplier_name)

    start_ts = _parse_date(start_date, "--startdate") if start_date is not None else None
    end_ts = _parse_date(end_date, "--enddate") if end_date is not None else None
    if start_ts is not None and end_ts is not None and start_ts > end_ts:
        print(f"--startdate ({start_date}) is after --enddate ({end_date}).")
        sys.exit(1)
    if start_ts is not None:
        target_df = target_df[target_df["order_date"] >= start_ts]
    if end_ts is not None:
        target_df = target_df[target_df["order_date"] <= end_ts]

    if target_df.empty:
        print(f"No orders found for supplier '{supplier_name}' in the given scope/date range.")
        sys.exit(1)

    label = commons.describe_filters(component_name, supplier_name)
    if start_date or end_date:
        label = f"{label} | {start_date or '...'} to {end_date or '...'}"

    component_breakdown = json.loads(
        compute_landed_cost(target_df, ["component_category"]).reset_index().to_json(orient="records")
    )
    criticality_breakdown = json.loads(
        compute_landed_cost(target_df, ["component_category", "component_criticality"])
        .reset_index().to_json(orient="records")
    )

    print_table("Landed Cost by Component", label, component_breakdown)
    print_table("Landed Cost by Component x Criticality", label, criticality_breakdown)

    payload = {
        "filters": {
            "component": component_name,
            "supplier": supplier_name,
            "start_date": start_date,
            "end_date": end_date,
        },
        "component_breakdown": component_breakdown,
        "criticality_breakdown": criticality_breakdown,
    }
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))
    print(f"Results written to: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--filepath", required=True)
    parser.add_argument("--supplier", required=True)
    parser.add_argument("--component", default=None)
    parser.add_argument("--startdate", default=None, help="YYYY-MM-DD, inclusive")
    parser.add_argument("--enddate", default=None, help="YYYY-MM-DD, inclusive")
    parser.add_argument("--output", default="supplier_landed_cost.json")
    args = parser.parse_args()
    main(args.filepath, args.supplier, args.component, args.startdate, args.enddate, args.output)
