"""Defect root-cause & schedule-impact analysis for a given component.

Breaks down manufacturing-defect events (has_md_event) by fault type
(md_fault_type) and quantifies schedule impact (days_lost_to_md) per
supplier and per project — signals supplier_scorecard.py's defect *rate*
alone doesn't surface.
"""
import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import commons


def _is_blank(series: pd.Series) -> bool:
    return series.isna().all()


def build_fault_type_breakdown(d: pd.DataFrame) -> pd.DataFrame:
    """Pareto of defect events by md_fault_type: frequency, rework cost, schedule cost."""
    defects = d[d["has_md_event"].fillna(False) == True].copy()
    defects["md_fault_type"] = defects["md_fault_type"].fillna("Unspecified")

    grouped = defects.groupby("md_fault_type").agg(
        defect_count=("order_id", "count"),
        total_rework_cost=("cost_of_rework_usd", "sum"),
        total_days_lost=("days_lost_to_md", "sum"),
        avg_days_lost=("days_lost_to_md", "mean"),
    ).reset_index()

    total_defects = grouped["defect_count"].sum()
    grouped["pct_of_defects"] = (
        grouped["defect_count"] / total_defects * 100 if total_defects else 0.0
    )
    return grouped.sort_values("defect_count", ascending=False).reset_index(drop=True)


def build_supplier_schedule_impact(d: pd.DataFrame, group_keys: list = ["supplier_name"]) -> pd.DataFrame:
    """Defect frequency, fault attribution, and total schedule days lost,
    grouped by `group_keys` (supplier alone by default; pass
    ["supplier_name", "component_criticality"] for the finer breakdown)."""
    defects = d[d["has_md_event"].fillna(False) == True].copy()

    grouped = defects.groupby(group_keys).agg(
        defect_count=("order_id", "count"),
        supplier_fault_count=("is_supplier_fault", lambda x: int(x.fillna(False).sum())),
        total_days_lost=("days_lost_to_md", "sum"),
        total_rework_cost=("cost_of_rework_usd", "sum"),
    ).reset_index()

    grouped["supplier_fault_pct"] = (
        grouped["supplier_fault_count"] / grouped["defect_count"] * 100
    )
    total_days = grouped["total_days_lost"].sum()
    grouped["pct_of_component_days_lost"] = (
        grouped["total_days_lost"] / total_days * 100 if total_days else 0.0
    )
    return grouped.sort_values("total_days_lost", ascending=False).reset_index(drop=True)


def build_project_schedule_impact(d: pd.DataFrame) -> pd.DataFrame:
    """Per-project defect frequency and total schedule days lost, when project_number is present."""
    defects = d[d["has_md_event"].fillna(False) == True].copy()
    if _is_blank(defects["project_number"]):
        return pd.DataFrame()

    grouped = defects.dropna(subset=["project_number"]).groupby("project_number").agg(
        defect_count=("order_id", "count"),
        total_days_lost=("days_lost_to_md", "sum"),
        suppliers_involved=("supplier_name", lambda x: sorted(x.unique())),
    ).reset_index()
    return grouped.sort_values("total_days_lost", ascending=False).reset_index(drop=True)


def plot_defect_root_cause(
    fault_breakdown: pd.DataFrame,
    supplier_impact: pd.DataFrame,
    label: str,
    output_path: str = "defect_root_cause_analysis.png",
) -> str:
    fig, axes = plt.subplots(1, 2, figsize=(14, max(6, 0.4 * max(len(fault_breakdown), len(supplier_impact)))))

    top_faults = fault_breakdown.head(10).iloc[::-1]
    axes[0].barh(top_faults["md_fault_type"], top_faults["defect_count"], color="#d62728", alpha=0.8)
    axes[0].set_xlabel("Defect Count")
    axes[0].set_title(f"Defect Type Pareto — {label}")

    top_suppliers = supplier_impact.head(10).iloc[::-1]
    axes[1].barh(top_suppliers["supplier_name"], top_suppliers["total_days_lost"], color="#1f77b4", alpha=0.8)
    axes[1].set_xlabel("Total Days Lost to Defects")
    axes[1].set_title(f"Supplier Schedule Impact — {label}")

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


def main(
    file_path: str,
    component_name: str,
    supplier_name: str = None,
    criticality_name: str = None,
    image_output: str = "defect_root_cause_analysis.png",
    json_output: str = "defect_root_cause_analysis.json",
) -> None:
    df = commons.load_dataset(file_path)
    commons.validate_filters(df, component=component_name, supplier=supplier_name, criticality=criticality_name)
    d = commons.filter_dataset(df, component=component_name, supplier=supplier_name, criticality=criticality_name)
    label = commons.describe_filters(component_name, supplier_name, criticality_name)

    if _is_blank(d["has_md_event"]):
        print(f"No 'has_md_event' data found for '{label}'; cannot run defect root-cause analysis.")
        return
    if _is_blank(d["md_fault_type"]) and _is_blank(d["days_lost_to_md"]):
        print(f"Neither 'md_fault_type' nor 'days_lost_to_md' present for '{label}'; nothing to analyze.")
        return

    fault_breakdown = build_fault_type_breakdown(d)
    supplier_impact = build_supplier_schedule_impact(d, ["supplier_name"])
    supplier_criticality_breakdown = build_supplier_schedule_impact(d, ["supplier_name", "component_criticality"])
    project_impact = build_project_schedule_impact(d)

    pd.set_option("display.width", 200)

    print(f"\nDefect Fault-Type Breakdown — {label}")
    print("-" * 80)
    print(fault_breakdown.round(2).to_string(index=False))

    print(f"\nSupplier Schedule Impact — {label}")
    print("-" * 80)
    print(supplier_impact.round(2).to_string(index=False))

    if not project_impact.empty:
        print(f"\nProject Schedule Impact — {label}")
        print("-" * 80)
        print(project_impact.round(2).to_string(index=False))

    saved_image = plot_defect_root_cause(fault_breakdown, supplier_impact, label, image_output)
    print(f"\nChart saved to: {saved_image}")

    filters = commons.filters_dict(component_name, supplier_name, criticality_name)
    result = {
        "filters": filters,
        "fault_type_breakdown": json.loads(fault_breakdown.round(2).to_json(orient="records")),
        "supplier_schedule_impact": json.loads(supplier_impact.round(2).to_json(orient="records")),
        "supplier_criticality_breakdown": json.loads(supplier_criticality_breakdown.round(2).to_json(orient="records")),
        "project_schedule_impact": (
            json.loads(project_impact.round(2).to_json(orient="records")) if not project_impact.empty else []
        ),
    }
    path = Path(json_output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=2))
    print(f"Results written to: {json_output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--filepath", required=True)
    parser.add_argument("--component", required=True)
    parser.add_argument("--supplier", default=None)
    parser.add_argument("--criticality", default=None)
    parser.add_argument("--image-output", default="defect_root_cause_analysis.png")
    parser.add_argument("--json-output", default="defect_root_cause_analysis.json")
    args = parser.parse_args()
    main(args.filepath, args.component, args.supplier, args.criticality, args.image_output, args.json_output)
