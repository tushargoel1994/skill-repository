import argparse
import json
from pathlib import Path

import pandas as pd
import commons

DATE_COLS = ["request_date", "commit_date", "received_date"]


def gap_stats(gap_days) -> dict:
    """Count/avg/std (and min/max) for a series of day-gaps, rounded for readability."""
    gap_days = gap_days.dropna()
    if gap_days.empty:
        return {"count": 0, "avg_days": None, "std_days": None, "min_days": None, "max_days": None}
    return {
        "count": int(gap_days.count()),
        "avg_days": round(float(gap_days.mean()), 2),
        "std_days": round(float(gap_days.std()), 2) if gap_days.count() > 1 else 0.0,
        "min_days": int(gap_days.min()),
        "max_days": int(gap_days.max()),
    }


def _gap_stats_for_group(sub: pd.DataFrame) -> dict:
    """For each criticality level, break POs into:
      - on_time_as_requested: delivered exactly on the originally requested date
      - committed_later: commit date pushed out past the request date (+ gap stats)
      - delayed_beyond_commit: delivered even later than the (possibly pushed-out)
        commit date (+ gap stats)
    """
    request_commit_gap = (sub["commit_date"] - sub["request_date"]).dt.days
    commit_actual_gap = (sub["received_date"] - sub["commit_date"]).dt.days
    on_time_as_requested = sub[request_commit_gap == 0]

    return {
        "total_pos": int(len(sub)),
        "on_time_as_requested": {"count": int(len(on_time_as_requested))},
        "committed_later": gap_stats(request_commit_gap[request_commit_gap > 0]),
        "delayed_beyond_commit": gap_stats(commit_actual_gap[commit_actual_gap > 0]),
    }


def flatten_gap_stats(stats: dict) -> dict:
    """Flatten _gap_stats_for_group's nested sub-objects into prefixed scalar
    columns, for the flat-array breakdown convention (component_breakdown /
    criticality_breakdown)."""
    flat = {"total_pos": stats["total_pos"], "on_time_as_requested_count": stats["on_time_as_requested"]["count"]}
    for bucket in ("committed_later", "delayed_beyond_commit"):
        for field in ("count", "avg_days", "std_days", "min_days", "max_days"):
            flat[f"{bucket}_{field}"] = stats[bucket][field]
    return flat


def build_breakdown(d: pd.DataFrame, group_keys: list) -> list:
    """One flat record per group in `group_keys`, sorted by total_pos
    descending."""
    records = []
    for key, sub in d.groupby(group_keys, dropna=True):
        key_tuple = key if isinstance(key, tuple) else (key,)
        row = dict(zip(group_keys, (str(k) for k in key_tuple)))
        row.update(flatten_gap_stats(_gap_stats_for_group(sub)))
        records.append(row)
    return sorted(records, key=lambda r: r["total_pos"], reverse=True)


def export_analysis(payload: dict, output_path: str = "request_commit_actual_gap.json") -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))
    return str(path)


def main(file_path, component_name=None, supplier_name=None, criticality_name=None,
         output_path="request_commit_actual_gap.json") -> None:
    """Read the file and export the request->commit->actual gap analysis as JSON.
    Requires --component or --supplier (never neither); when --component is
    omitted, results are broken down by component_category as well."""
    df = commons.load_dataset(file_path, extra_date_cols=DATE_COLS)
    commons.require_component_or_supplier(component_name, supplier_name, context="request_commit_actual_gap")
    commons.validate_filters(df, component=component_name, supplier=supplier_name, criticality=criticality_name)
    d = commons.filter_dataset(df, component=component_name, supplier=supplier_name, criticality=criticality_name)
    label = commons.describe_filters(component_name, supplier_name, criticality_name)

    if d["component_criticality"].dropna().empty:
        print(f"No 'component_criticality' values found for '{label}'; nothing to analyze.")
        return

    if component_name is not None:
        component_breakdown = [flatten_gap_stats(_gap_stats_for_group(d))]
        criticality_breakdown = build_breakdown(d, ["component_criticality"])
    else:
        component_breakdown = build_breakdown(d, ["component_category"])
        criticality_breakdown = build_breakdown(d, ["component_category", "component_criticality"])

    filters = commons.filters_dict(component_name, supplier_name, criticality_name)
    payload = {"filters": filters, "component_breakdown": component_breakdown, "criticality_breakdown": criticality_breakdown}
    saved_path = export_analysis(payload, output_path)
    print(f"Request/commit/actual gap analysis written to: {saved_path}")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--filepath", required=True)
    parser.add_argument("--component", default=None)
    parser.add_argument("--supplier", default=None)
    parser.add_argument("--criticality", default=None)
    parser.add_argument("--output", default="request_commit_actual_gap.json")
    args = parser.parse_args()
    main(args.filepath, args.component, args.supplier, args.criticality, args.output)
