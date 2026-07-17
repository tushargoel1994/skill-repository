
import argparse
import json
from pathlib import Path

import commons

def compute_summary(d) -> dict:
    """Compute the summary fields for the given (already-filtered) dataframe."""
    total_spend = d["line_spend_usd"].sum()
    total_qty = d["qty_ordered"].sum()
    ontime_pct = (1 - d["is_late_arrived"].fillna(False).mean()) * 100
    md_rate = d["has_md_event"].fillna(False).mean() * 100

    return {
        "total_spend": round(float(total_spend), 2),
        "total_qty": int(total_qty),
        "po_count": int(len(d)),
        "active_suppliers": int(d["supplier_name"].nunique()),
        "projects_touched": int(d["project_number"].nunique()),
        "ontime_pct": round(float(ontime_pct), 2),
        "md_rate": round(float(md_rate), 2),
        "total_rework_cost": round(float(d["cost_of_rework_usd"].sum()), 2),
        "open_late_pos": int(d["is_open_late"].fillna(False).sum()),
    }


def print_summary_tile(summary: dict, label: str) -> None:
    """Print summary tile from an already-computed summary dict."""
    print()
    print("=" * 60)
    print(f"  COMPONENT SUMMARY — {label}")
    print("=" * 60)
    print(f"  Total spend:        ${summary['total_spend']:,.0f}")
    print(f"  Total qty ordered:  {summary['total_qty']:,}")
    print(f"  Number of POs:      {summary['po_count']}")
    print(f"  Active suppliers:   {summary['active_suppliers']}")
    print(f"  Projects touched:   {summary['projects_touched']}")
    print(f"  On-time delivery:   {summary['ontime_pct']:.1f}%")
    print(f"  MD event rate:      {summary['md_rate']:.1f}%")
    print(f"  Total rework cost:  ${summary['total_rework_cost']:,.0f}")
    print(f"  Open-late POs:      {summary['open_late_pos']}")
    print("=" * 60)
    print()


def export_summary_json(payload: dict, output_path: str = "component_summary.json") -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))
    return str(path)


def main(file_path, component_name, supplier_name=None, criticality_name=None,
         output_path="component_summary.json"):
    """Read the file, print the summary, and export it as JSON."""
    df = commons.load_dataset(file_path)
    commons.validate_filters(df, component=component_name, supplier=supplier_name, criticality=criticality_name)
    d = commons.filter_dataset(df, component=component_name, supplier=supplier_name, criticality=criticality_name)
    label = commons.describe_filters(component_name, supplier_name, criticality_name)

    summary = compute_summary(d)
    print_summary_tile(summary, label)

    component_breakdown = [summary]
    criticality_breakdown = [
        {"component_criticality": str(crit), **compute_summary(sub)}
        for crit, sub in d.groupby("component_criticality", dropna=True)
    ]

    filters = commons.filters_dict(component_name, supplier_name, criticality_name)
    payload = {"filters": filters, "component_breakdown": component_breakdown, "criticality_breakdown": criticality_breakdown}
    saved_path = export_summary_json(payload, output_path)
    print(f"Summary written to: {saved_path}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--filepath", required=True)
    parser.add_argument("--component", required=True)
    parser.add_argument("--supplier", default=None)
    parser.add_argument("--criticality", default=None)
    parser.add_argument("--output", default="component_summary.json")
    args = parser.parse_args()
    main(args.filepath, args.component, args.supplier, args.criticality, args.output)
