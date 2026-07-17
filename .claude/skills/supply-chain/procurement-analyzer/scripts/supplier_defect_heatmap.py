"""MD (defect) rate by component x quarter, for a single target supplier.

Adapted from datasets/1-supplier-stability-dateset-for-procurement/scripts/
supplier_report.py's plot_defect_heatmap. Two corrections from the original:

1. The original sorts quarter columns with a plain `sorted()` on strings
   like "Q1-2024"/"Q2-2024" — that's a LEXICAL sort, not chronological, so
   e.g. "Q1-2025" sorts before "Q2-2024" even though Q2-2024 happened
   first. This version parses (year, quarter_number) and sorts on that.
2. The original doesn't check whether has_md_event is populated at all —
   if it's entirely blank, it would still render a heatmap of all-0%
   defect rates, indistinguishable from "genuinely zero defects." This
   version exits with a clear message instead (same check
   defect_root_cause_analysis.py already uses).
"""
import argparse
import json
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import commons


def _quarter_sort_key(q):
    """Parse 'Q<n>-<yyyy>' into a (year, quarter_number) tuple for correct
    chronological sorting. Unparseable values sort first."""
    m = re.match(r"Q(\d+)-(\d+)", str(q))
    if m:
        return (int(m.group(2)), int(m.group(1)))
    return (0, 0)


def compute_defect_matrix(d: pd.DataFrame) -> pd.DataFrame:
    dd = d.copy()
    dd["md_flag"] = dd["has_md_event"].fillna(False).astype(int)
    agg = dd.groupby(["component_category", "quarter"]).agg(
        po_count=("order_id", "count"),
        defect_count=("md_flag", "sum"),
    ).reset_index()
    agg["md_rate_pct"] = (agg["defect_count"] / agg["po_count"] * 100).round(2)
    agg["_sort_key"] = agg["quarter"].apply(_quarter_sort_key)
    agg = agg.sort_values(["component_category", "_sort_key"]).drop(columns="_sort_key")
    return agg


def plot_defect_heatmap(d: pd.DataFrame, label: str, output_path: str) -> str:
    dd = d.copy()
    dd["md_flag"] = dd["has_md_event"].fillna(False).astype(int)
    pivot = dd.pivot_table(index="component_category", columns="quarter", values="md_flag", aggfunc="mean") * 100
    quarters_sorted = sorted(pivot.columns, key=_quarter_sort_key)
    pivot = pivot.reindex(quarters_sorted, axis=1)

    fig, ax = plt.subplots(figsize=(10, max(5, len(pivot) * 0.5)))
    ax.set_title(f"MD Rate Heatmap: Component × Quarter (%) — {label}")
    sns.heatmap(pivot, annot=True, fmt=".0f", cmap="Reds", linewidths=0.5,
                cbar_kws={"label": "MD Rate (%)"}, ax=ax)
    ax.set_xlabel("Quarter")
    ax.set_ylabel("Component")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


def main(file_path, supplier_name,
         image_output="supplier_defect_heatmap.png",
         json_output="supplier_defect_heatmap.json") -> None:
    df = commons.load_dataset(file_path)
    commons.validate_filters(df, supplier=supplier_name)
    target_df = commons.filter_dataset(df, supplier=supplier_name)

    if target_df["has_md_event"].isna().all():
        print(f"No 'has_md_event' data found for supplier '{supplier_name}'; cannot build defect heatmap.")
        sys.exit(1)
    if target_df["quarter"].dropna().empty:
        print(f"No 'quarter' values found for supplier '{supplier_name}'; cannot build defect heatmap.")
        sys.exit(1)

    label = commons.describe_filters(supplier=supplier_name)
    matrix = compute_defect_matrix(target_df)
    records = json.loads(matrix.to_json(orient="records"))

    print(f"\nMD Rate by Component x Quarter — {label}")
    print("-" * 80)
    print(matrix.to_string(index=False))
    print()

    saved_image = plot_defect_heatmap(target_df, label, image_output)
    print(f"Heatmap saved to: {saved_image}")

    filters = commons.filters_dict(supplier=supplier_name)
    payload = {"filters": filters, "component_quarter_defect_rate": records}
    path = Path(json_output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))
    print(f"Results written to: {json_output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--filepath", required=True)
    parser.add_argument("--supplier", required=True)
    parser.add_argument("--image-output", default="supplier_defect_heatmap.png")
    parser.add_argument("--json-output", default="supplier_defect_heatmap.json")
    args = parser.parse_args()
    main(args.filepath, args.supplier, args.image_output, args.json_output)
