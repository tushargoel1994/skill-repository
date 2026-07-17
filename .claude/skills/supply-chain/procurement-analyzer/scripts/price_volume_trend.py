import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import commons


def plot_price_volume_trend(d: pd.DataFrame, label: str,
                             output_path: str = "price_volume_trend.png") -> str:
    """Combo chart: monthly avg unit price with 3-month rolling average
    (line, left axis) alongside monthly volume purchased (bar, right axis)."""
    monthly_price = d.groupby("order_month")["unit_cost_usd"].mean().sort_index()
    rolling = monthly_price.rolling(window=3, min_periods=1).mean()
    monthly_qty = d.groupby("order_month")["qty_ordered"].sum().sort_index()

    fig, ax1 = plt.subplots(figsize=(10, 6))
    ax1.set_title(f"Avg Unit Price & Volume Trend (3-mo Rolling) — {label}")
    ax2 = ax1.twinx()

    ax2.bar(monthly_qty.index, monthly_qty.values, width=20,
            alpha=0.3, color="gray", label="Monthly volume")
    ax1.plot(monthly_price.index, monthly_price.values, marker="o", alpha=0.4,
             label="Monthly avg price")
    ax1.plot(rolling.index, rolling.values, marker="o", linewidth=2,
             label="3-mo rolling price")

    # Keep the price lines drawn on top of the volume bars
    ax1.set_zorder(ax2.get_zorder() + 1)
    ax1.patch.set_visible(False)

    ax1.set_xlabel("Month")
    ax1.set_ylabel("Avg Unit Price (USD)")
    ax2.set_ylabel("Volume Purchased (qty)")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left")

    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


def compute_monthly_trend(d: pd.DataFrame, group_keys: list) -> list:
    """Monthly avg unit price (intentionally unweighted — a plain per-month
    mean is the right choice for a price-movement trend line, see issues_2.md
    #1) and volume purchased, grouped by `group_keys` (order_month alone, or
    order_month + component_criticality for the finer breakdown)."""
    agg = d.groupby(group_keys).agg(
        avg_unit_price=("unit_cost_usd", "mean"),
        total_qty=("qty_ordered", "sum"),
    ).reset_index()
    agg["order_month"] = agg["order_month"].astype(str)
    return agg.round(2).to_dict(orient="records")


def export_trend_json(component_breakdown: list, criticality_breakdown: list, filters: dict,
                       output_path: str = "price_volume_trend.json") -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "filters": filters,
        "component_breakdown": component_breakdown,
        "criticality_breakdown": criticality_breakdown,
    }
    path.write_text(json.dumps(payload, indent=2))
    return str(path)


def main(file_path, component_name, supplier_name=None, criticality_name=None,
         output_path="price_volume_trend.png", json_output="price_volume_trend.json") -> None:
    """Read the file, save the price/volume trend combo chart, and export the
    monthly trend (component-level and component x criticality) as JSON."""
    df = commons.load_dataset(file_path)
    commons.validate_filters(df, component=component_name, supplier=supplier_name, criticality=criticality_name)
    d = commons.filter_dataset(df, component=component_name, supplier=supplier_name, criticality=criticality_name).copy()
    label = commons.describe_filters(component_name, supplier_name, criticality_name)
    d["order_month"] = d["order_date"].dt.to_period("M").dt.to_timestamp()

    saved_path = plot_price_volume_trend(d, label, output_path)
    print(f"Plot saved to: {saved_path}")

    component_breakdown = compute_monthly_trend(d, ["order_month"])
    criticality_breakdown = compute_monthly_trend(d, ["order_month", "component_criticality"])
    filters = commons.filters_dict(component_name, supplier_name, criticality_name)
    saved_json = export_trend_json(component_breakdown, criticality_breakdown, filters, json_output)
    print(f"Monthly trend written to: {saved_json}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--filepath", required=True)
    parser.add_argument("--component", required=True)
    parser.add_argument("--supplier", default=None)
    parser.add_argument("--criticality", default=None)
    parser.add_argument("--output", default="price_volume_trend.png")
    parser.add_argument("--json-output", default="price_volume_trend.json")
    args = parser.parse_args()
    main(args.filepath, args.component, args.supplier, args.criticality, args.output, args.json_output)
