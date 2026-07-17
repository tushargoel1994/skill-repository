"""Project x component (and, in the JSON, project x component x criticality)
spend matrix for a target supplier.

Adapted from datasets/1-supplier-stability-dateset-for-procurement/scripts/
supplier_report.py's plot_project_component_matrix (heatmap of spend by
project x component). The heatmap stays component-level only, matching the
original; the JSON additionally includes a finer project x component x
criticality breakdown the original didn't have.

--project is a filter dimension commons.py doesn't support (same as
supplier_share_breakdown.py), so handled locally here.
"""
import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import commons


def _validate_project(df: pd.DataFrame, project) -> None:
    commons.require_columns(df, ["project_number"], "project lookup")
    available = sorted(df["project_number"].dropna().unique())
    if project not in available:
        print(f"Project '{project}' not present in the data.")
        print(f"Available project values: {', '.join(map(str, available))}")
        sys.exit(1)


def compute_matrix(d: pd.DataFrame, group_keys: list) -> pd.DataFrame:
    return (
        d.groupby(group_keys)
        .agg(po_count=("order_id", "count"), total_qty=("qty_ordered", "sum"), total_spend=("line_spend_usd", "sum"))
        .round(2)
        .reset_index()
        .sort_values(group_keys[:1] + ["total_spend"], ascending=[True] + [False])
    )


def plot_project_component_heatmap(d: pd.DataFrame, label: str, output_path: str) -> str:
    pivot = d.pivot_table(index="project_number", columns="component_category",
                           values="line_spend_usd", aggfunc="sum", fill_value=0)
    fig, ax = plt.subplots(figsize=(10, max(6, len(pivot) * 0.4)))
    ax.set_title(f"Project × Component Spend Matrix — {label}")
    sns.heatmap(pivot, annot=True, fmt=".0f", cmap="Blues", ax=ax)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


def print_matrix(title: str, label: str, rows: list) -> None:
    print(f"\n{title} — {label}")
    print("-" * 110)
    print(pd.DataFrame(rows).to_string(index=False) if rows else "No data.")
    print()


def main(file_path, supplier_name, component_name=None, project_name=None,
         image_output="supplier_project_component_matrix.png",
         json_output="supplier_project_component_matrix.json") -> None:
    df = commons.load_dataset(file_path)
    commons.validate_filters(df, component=component_name, supplier=supplier_name)
    if project_name is not None:
        _validate_project(df, project_name)

    target_df = commons.filter_dataset(df, component=component_name, supplier=supplier_name)
    if project_name is not None:
        target_df = target_df[target_df["project_number"] == project_name]
        if target_df.empty:
            print(f"No rows for supplier '{supplier_name}' in project '{project_name}' (within the given scope).")
            sys.exit(1)

    if target_df["project_number"].dropna().empty:
        print(f"No 'project_number' values found for supplier '{supplier_name}'; cannot build project x component matrix.")
        sys.exit(1)

    label = commons.describe_filters(component_name, supplier_name)
    if project_name is not None:
        label = f"{label} | Project={project_name}"

    component_matrix = compute_matrix(target_df, ["project_number", "component_category"])
    criticality_matrix = compute_matrix(target_df, ["project_number", "component_category", "component_criticality"])

    component_records = json.loads(component_matrix.to_json(orient="records"))
    criticality_records = json.loads(criticality_matrix.to_json(orient="records"))

    print_matrix("Project x Component Matrix", label, component_records)
    print_matrix("Project x Component x Criticality Matrix", label, criticality_records)

    saved_image = plot_project_component_heatmap(target_df, label, image_output)
    print(f"Heatmap saved to: {saved_image}")

    payload = {
        "filters": {"component": component_name, "supplier": supplier_name, "project": project_name},
        "component_breakdown": component_records,
        "criticality_breakdown": criticality_records,
    }
    path = Path(json_output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))
    print(f"Full matrix written to: {json_output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--filepath", required=True)
    parser.add_argument("--supplier", required=True)
    parser.add_argument("--component", default=None)
    parser.add_argument("--project", default=None)
    parser.add_argument("--image-output", default="supplier_project_component_matrix.png")
    parser.add_argument("--json-output", default="supplier_project_component_matrix.json")
    args = parser.parse_args()
    main(args.filepath, args.supplier, args.component, args.project, args.image_output, args.json_output)
