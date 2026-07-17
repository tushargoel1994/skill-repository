"""Price trend of a target supplier vs. all other suppliers of the same
component, split into one line chart per criticality tier the target
supplier actually serves within that component.

Adapted from datasets/1-supplier-stability-dateset-for-procurement/scripts/
supplier_report.py's plot_price_trend_by_category (small-multiples grid of
monthly avg unit price per category), extended with a second "all other
suppliers" comparison line on each subplot and split by criticality instead
of component (component is fixed here via the required --component arg).
"""
import argparse
import json
import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import commons


def monthly_avg_price(d: pd.DataFrame) -> pd.Series:
    if d.empty:
        return pd.Series(dtype=float)
    dd = d.copy()
    dd["order_month"] = dd["order_date"].dt.to_period("M").dt.to_timestamp()
    return dd.groupby("order_month")["unit_cost_usd"].mean().sort_index()


def series_to_records(s: pd.Series) -> list:
    return [{"month": idx.date().isoformat(), "avg_price": round(float(v), 2)} for idx, v in s.items()]


def build_facet_data(target_df: pd.DataFrame, peer_df: pd.DataFrame, facet_col: str) -> dict:
    """One entry per value of facet_col the target supplier actually has
    orders in (mirrors plot_price_trend_by_category's own scoping to
    self.supp_df's categories, not every value in the dataset)."""
    facet_values = sorted(target_df[facet_col].dropna().unique())
    data = {}
    for val in facet_values:
        t_sub = target_df[target_df[facet_col] == val]
        p_sub = peer_df[peer_df[facet_col] == val]
        data[val] = {
            "target": monthly_avg_price(t_sub),
            "peer": monthly_avg_price(p_sub),
            "target_po_count": int(len(t_sub)),
            "peer_po_count": int(len(p_sub)),
        }
    return data


def plot_price_trend_grid(facet_data: dict, facet_label: str, supplier_name: str,
                           chart_title: str, output_path: str) -> str:
    keys = sorted(facet_data.keys())
    if not keys:
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.text(0.5, 0.5, "No data", ha="center", va="center")
        ax.set_title(chart_title)
        plt.tight_layout()
        plt.savefig(output_path, dpi=150)
        plt.close(fig)
        return output_path

    ncols = min(3, len(keys))
    nrows = math.ceil(len(keys) / ncols)
    fig, axes = plt.subplots(nrows, ncols, figsize=(5.5 * ncols, 4 * nrows), squeeze=False)
    fig.suptitle(chart_title)

    for i, key in enumerate(keys):
        ax = axes[i // ncols][i % ncols]
        target_series = facet_data[key]["target"]
        peer_series = facet_data[key]["peer"]
        if not target_series.empty:
            ax.plot(target_series.index, target_series.values, marker="o", label=supplier_name)
        if not peer_series.empty:
            ax.plot(peer_series.index, peer_series.values, marker="o", linestyle="--", label="All other suppliers")
        ax.set_title(f"{facet_label}: {key}", fontsize=10)
        ax.tick_params(axis="x", rotation=30)
        ax.legend(fontsize=8)

    for j in range(len(keys), nrows * ncols):
        axes[j // ncols][j % ncols].axis("off")

    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


def _print_series_table(records: list) -> None:
    if not records:
        print("    No data.")
        return
    for line in pd.DataFrame(records).to_string(index=False).splitlines():
        print(f"    {line}")


def print_facet_data(label: str, facet_data: dict, supplier_name: str) -> None:
    print(f"\nPrice Trend by Criticality — {label}")
    print("-" * 80)
    for crit, d in facet_data.items():
        print(f"\nCriticality: {crit}  (target POs: {d['target_po_count']}, peer POs: {d['peer_po_count']})")
        print(f"  {supplier_name}:")
        _print_series_table(series_to_records(d["target"]))
        print("  All other suppliers:")
        _print_series_table(series_to_records(d["peer"]))
    print()


def main(file_path, supplier_name, component_name,
         image_output="supplier_price_trend_by_criticality.png",
         json_output="supplier_price_trend_by_criticality.json") -> None:
    df = commons.load_dataset(file_path)
    commons.validate_filters(df, component=component_name, supplier=supplier_name)

    component_scope_df = commons.filter_dataset(df, component=component_name)
    target_df = component_scope_df[component_scope_df["supplier_name"] == supplier_name]
    peer_df = component_scope_df[component_scope_df["supplier_name"] != supplier_name]

    if target_df.empty:
        print(f"No orders found for supplier '{supplier_name}' in component '{component_name}'.")
        sys.exit(1)

    label = commons.describe_filters(component_name, supplier_name)
    facet_data = build_facet_data(target_df, peer_df, "component_criticality")

    print_facet_data(label, facet_data, supplier_name)

    chart_title = f"Price Trend by Criticality — {label}"
    saved_image = plot_price_trend_grid(facet_data, "Criticality", supplier_name, chart_title, image_output)
    print(f"Chart saved to: {saved_image}")

    filters = commons.filters_dict(component_name, supplier_name)
    payload = {
        "filters": filters,
        "by_criticality": {
            str(crit): {
                "target_po_count": d["target_po_count"],
                "peer_po_count": d["peer_po_count"],
                "target_supplier_monthly_avg_price": series_to_records(d["target"]),
                "peer_suppliers_monthly_avg_price": series_to_records(d["peer"]),
            }
            for crit, d in facet_data.items()
        },
    }
    path = Path(json_output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))
    print(f"Results written to: {json_output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--filepath", required=True)
    parser.add_argument("--supplier", required=True)
    parser.add_argument("--component", required=True)
    parser.add_argument("--image-output", default="supplier_price_trend_by_criticality.png")
    parser.add_argument("--json-output", default="supplier_price_trend_by_criticality.json")
    args = parser.parse_args()
    main(args.filepath, args.supplier, args.component, args.image_output, args.json_output)
