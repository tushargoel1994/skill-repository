"""Supplier share of each component and component-criticality tier: qty,
POs, spend, delay burden, and delayed % — plus this supplier's % share of
qty and spend against the peer set in the same scope, at both a
component-level and a finer (component, criticality)-level breakdown.

Adapted from datasets/1-supplier-stability-dateset-for-procurement/scripts/
supplier_report.py's plot_share_of_category (share-of-category spend chart,
dominance threshold), extended with a quantity share alongside the spend
share, delay metrics, and a criticality-level breakdown on top of the
component-level one.

--project is a filter dimension commons.py doesn't support (the rest of the
skill's scripts don't use it), so it's handled locally here rather than
changing commons.py's shared contract, which the other scripts' JSON
schemas already pin down with additionalProperties: false.
"""
import argparse
import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import commons

DOMINANCE_THRESHOLD_PCT = 25.0


def _validate_project(df: pd.DataFrame, project) -> None:
    commons.require_columns(df, ["project_number"], "project lookup")
    available = sorted(df["project_number"].dropna().unique())
    if project not in available:
        print(f"Project '{project}' not present in the data.")
        print(f"Available project values: {', '.join(map(str, available))}")
        sys.exit(1)


def compute_share_breakdown(peer_df: pd.DataFrame, supp_df: pd.DataFrame, group_keys: list) -> pd.DataFrame:
    """`peer_df` is the scope WITHOUT the supplier filter (the market);
    `supp_df` is the same scope WITH the supplier filter. group_keys is
    either ["component_category"] or ["component_category", "component_criticality"]."""
    peer_qty = peer_df.groupby(group_keys)["qty_ordered"].sum()
    peer_spend = peer_df.groupby(group_keys)["line_spend_usd"].sum()

    agg = supp_df.groupby(group_keys).agg(
        po_count=("order_id", "count"),
        qty=("qty_ordered", "sum"),
        total_spend=("line_spend_usd", "sum"),
        delayed_po_count=("is_late_arrived", lambda x: int(x.fillna(False).sum())),
    )
    agg["delayed_pct"] = agg["delayed_po_count"] / agg["po_count"] * 100

    late_days = supp_df[supp_df["days_late"] > 0].groupby(group_keys)["days_late"].sum()
    agg["total_days_delayed"] = late_days.reindex(agg.index).fillna(0)

    agg["qty_share_pct"] = agg["qty"] / peer_qty.reindex(agg.index) * 100
    agg["spend_share_pct"] = agg["total_spend"] / peer_spend.reindex(agg.index) * 100
    agg["is_dominant_supplier"] = agg["spend_share_pct"] >= DOMINANCE_THRESHOLD_PCT

    return agg.round(2).sort_values("total_spend", ascending=False)


def _row_label(df_chart: pd.DataFrame) -> pd.Series:
    if "component_criticality" in df_chart.columns:
        return df_chart["component_category"] + " / " + df_chart["component_criticality"]
    return df_chart["component_category"]


def plot_share_chart(rows: list, metric_key: str, chart_title: str, label: str, output_path: str,
                      dominance_pct: float = DOMINANCE_THRESHOLD_PCT) -> str:
    """Horizontal bar of `metric_key` (a share %) per (component[, criticality])
    row, dominance line drawn in — mirrors plot_share_of_category's style."""
    df_chart = pd.DataFrame(rows)
    fig, ax = plt.subplots(figsize=(10, max(6, 0.35 * max(len(df_chart), 1))))

    if df_chart.empty:
        ax.text(0.5, 0.5, "No data", ha="center", va="center")
    else:
        df_chart = df_chart.assign(row_label=_row_label(df_chart)).sort_values(metric_key, ascending=True)
        colors = ["#d62728" if v >= dominance_pct else "steelblue" for v in df_chart[metric_key]]
        ax.barh(df_chart["row_label"], df_chart[metric_key], color=colors)
        ax.axvline(dominance_pct, color="red", linestyle="--", label=f"Dominance line ({dominance_pct:.0f}%)")
        ax.legend()

    ax.set_xlabel(f"{chart_title} (%)")
    ax.set_title(f"{chart_title} — {label}")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


def print_breakdown(title: str, label: str, rows: list) -> None:
    print(f"\n{title} — {label}")
    print("-" * 110)
    print(pd.DataFrame(rows).to_string(index=False) if rows else "No data.")
    print()


def main(file_path, supplier_name, component_name=None, project_name=None,
         qty_chart_output="supplier_share_quantity.png",
         spend_chart_output="supplier_share_spend.png",
         json_output="supplier_share_breakdown.json") -> None:
    df = commons.load_dataset(file_path)
    commons.validate_filters(df, component=component_name, supplier=supplier_name)
    if project_name is not None:
        _validate_project(df, project_name)

    peer_df = commons.filter_dataset(df, component=component_name)
    supp_df = commons.filter_dataset(df, component=component_name, supplier=supplier_name)
    if project_name is not None:
        peer_df = peer_df[peer_df["project_number"] == project_name]
        supp_df = supp_df[supp_df["project_number"] == project_name]
        if supp_df.empty:
            print(f"No rows for supplier '{supplier_name}' in project '{project_name}' (within the given scope).")
            sys.exit(1)

    label = commons.describe_filters(component_name, supplier_name)
    if project_name is not None:
        label = f"{label} | Project={project_name}"

    component_breakdown = json.loads(
        compute_share_breakdown(peer_df, supp_df, ["component_category"]).reset_index().to_json(orient="records")
    )
    criticality_breakdown = json.loads(
        compute_share_breakdown(peer_df, supp_df, ["component_category", "component_criticality"])
        .reset_index().to_json(orient="records")
    )

    print_breakdown("Component-Level Share Breakdown", label, component_breakdown)
    print_breakdown("Component x Criticality Share Breakdown", label, criticality_breakdown)

    saved_qty_chart = plot_share_chart(
        criticality_breakdown, "qty_share_pct", "Quantity Share", label, qty_chart_output
    )
    print(f"Quantity share chart saved to: {saved_qty_chart}")

    saved_spend_chart = plot_share_chart(
        criticality_breakdown, "spend_share_pct", "Spend Share", label, spend_chart_output
    )
    print(f"Spend share chart saved to: {saved_spend_chart}")

    payload = {
        "filters": {"component": component_name, "supplier": supplier_name, "project": project_name},
        "component_breakdown": component_breakdown,
        "criticality_breakdown": criticality_breakdown,
    }
    path = Path(json_output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))
    print(f"Full breakdown written to: {json_output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--filepath", required=True)
    parser.add_argument("--supplier", required=True)
    parser.add_argument("--component", default=None)
    parser.add_argument("--project", default=None)
    parser.add_argument("--qty-chart-output", default="supplier_share_quantity.png")
    parser.add_argument("--spend-chart-output", default="supplier_share_spend.png")
    parser.add_argument("--json-output", default="supplier_share_breakdown.json")
    args = parser.parse_args()
    main(args.filepath, args.supplier, args.component, args.project,
         args.qty_chart_output, args.spend_chart_output, args.json_output)
