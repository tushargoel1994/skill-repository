import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import commons

LOW_VOLUME_PCT = 5.0
HEALTHY_VOLUME_PCT = 15.0

CHEAP_PRICE_PERCENTILE = 0.30
EXPENSIVE_PRICE_PERCENTILE = 0.70


def categorize_volume(volume_pct, low_volume_pct=LOW_VOLUME_PCT, healthy_volume_pct=HEALTHY_VOLUME_PCT) -> str:
    if volume_pct < low_volume_pct:
        return "Low Volume"
    if volume_pct <= healthy_volume_pct:
        return "Healthy Volume"
    return "Strategic Supplier"


def categorize_price(price_percentile, cheap_pct=CHEAP_PRICE_PERCENTILE, expensive_pct=EXPENSIVE_PRICE_PERCENTILE) -> str:
    if price_percentile <= cheap_pct:
        return "Cheaper"
    if price_percentile <= expensive_pct:
        return "Acceptable"
    return "Expensive"


def categorize_suppliers(
    d: pd.DataFrame,
    group_keys: list = ["supplier_name"],
    low_volume_pct=LOW_VOLUME_PCT,
    healthy_volume_pct=HEALTHY_VOLUME_PCT,
    cheap_price_percentile=CHEAP_PRICE_PERCENTILE,
    expensive_price_percentile=EXPENSIVE_PRICE_PERCENTILE,
) -> pd.DataFrame:
    """Categorize each group (by default one row per supplier; pass
    group_keys=["supplier_name", "component_criticality"] for the finer
    breakdown) in `d` (already filtered by the caller) by price charged and
    volume contributed. volume_pct/price_percentile are computed relative to
    whichever population `group_keys` produces."""
    agg = d.groupby(group_keys).agg(
        total_qty=("qty_ordered", "sum"),
        total_spend=("line_spend_usd", "sum"),
    ).reset_index()

    agg["avg_price"] = agg["total_spend"] / agg["total_qty"]
    agg["volume_pct"] = agg["total_qty"] / agg["total_qty"].sum() * 100
    agg["price_percentile"] = agg["avg_price"].rank(pct=True)

    agg["volume_category"] = agg["volume_pct"].apply(
        lambda v: categorize_volume(v, low_volume_pct, healthy_volume_pct)
    )
    agg["price_category"] = agg["price_percentile"].apply(
        lambda p: categorize_price(p, cheap_price_percentile, expensive_price_percentile)
    )
    agg["segment"] = agg["price_category"] + " / " + agg["volume_category"]

    return agg.sort_values("total_spend", ascending=False).reset_index(drop=True)


def print_categorized_suppliers(agg: pd.DataFrame, label: str) -> None:
    cols = ["supplier_name", "avg_price", "volume_pct", "price_category", "volume_category", "segment"]
    print(f"\nSupplier Price/Volume Categorization — {label}")
    print("-" * 90)
    print(agg[cols].round(2).to_string(index=False))
    print()


SEGMENT_COLORS = {"Cheaper": "#2ca02c", "Acceptable": "#1f77b4", "Expensive": "#d62728"}


def plot_price_volume_scatter(
    agg: pd.DataFrame,
    label: str,
    low_volume_pct=LOW_VOLUME_PCT,
    healthy_volume_pct=HEALTHY_VOLUME_PCT,
    cheap_price_percentile=CHEAP_PRICE_PERCENTILE,
    expensive_price_percentile=EXPENSIVE_PRICE_PERCENTILE,
    output_path="price_volume_scatter.png",
) -> str:
    """Scatter of avg price vs. volume contribution with the categorization boundaries drawn in."""
    fig, ax = plt.subplots(figsize=(10, 6))
    sizes = agg["total_spend"] / agg["total_spend"].max() * 500 + 20

    for category, color in SEGMENT_COLORS.items():
        sub = agg[agg["price_category"] == category]
        ax.scatter(sub["avg_price"], sub["volume_pct"], s=sizes.loc[sub.index],
                   alpha=0.6, color=color, label=category)

    for _, r in agg.iterrows():
        ax.annotate(r["supplier_name"], (r["avg_price"], r["volume_pct"]),
                    fontsize=8, alpha=0.7)

    # Volume boundaries: Low Volume / Healthy / Strategic Supplier
    ax.axhline(low_volume_pct, color="gray", linestyle="--", linewidth=1)
    ax.axhline(healthy_volume_pct, color="gray", linestyle="--", linewidth=1)

    # Price boundaries: Cheaper / Acceptable / Expensive (percentile -> actual price)
    cheap_price = agg["avg_price"].quantile(cheap_price_percentile)
    expensive_price = agg["avg_price"].quantile(expensive_price_percentile)
    ax.axvline(cheap_price, color="gray", linestyle=":", linewidth=1)
    ax.axvline(expensive_price, color="gray", linestyle=":", linewidth=1)

    ax.set_xlabel("Avg Unit Price (USD)")
    ax.set_ylabel("Volume Contribution (%)")
    ax.set_title(f"Supplier Price vs. Volume — {label}")
    ax.legend(title="Price Category")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


def export_price_volume_json(component_breakdown: pd.DataFrame, criticality_breakdown: pd.DataFrame,
                              filters: dict, output_path: str = "price_volume_scatter.json") -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "filters": filters,
        "component_breakdown": json.loads(component_breakdown.round(2).to_json(orient="records")),
        "criticality_breakdown": json.loads(criticality_breakdown.round(2).to_json(orient="records")),
    }
    path.write_text(json.dumps(payload, indent=2))
    return str(path)


def main(file_path, component_name, supplier_name=None, criticality_name=None,
         image_output="price_volume_scatter.png", json_output="price_volume_scatter.json") -> None:
    """Read the file, print supplier price/volume categorization, save the
    scatter plot, and export the categorization table as JSON."""
    df = commons.load_dataset(file_path)
    commons.validate_filters(df, component=component_name, supplier=supplier_name, criticality=criticality_name)
    d = commons.filter_dataset(df, component=component_name, supplier=supplier_name, criticality=criticality_name)
    label = commons.describe_filters(component_name, supplier_name, criticality_name)

    component_breakdown = categorize_suppliers(d, ["supplier_name"])
    criticality_breakdown = categorize_suppliers(d, ["supplier_name", "component_criticality"])
    print_categorized_suppliers(component_breakdown, label)

    saved_image = plot_price_volume_scatter(component_breakdown, label, output_path=image_output)
    print(f"Plot saved to: {saved_image}")

    filters = commons.filters_dict(component_name, supplier_name, criticality_name)
    saved_json = export_price_volume_json(component_breakdown, criticality_breakdown, filters, json_output)
    print(f"Categorization written to: {saved_json}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--filepath", required=True)
    parser.add_argument("--component", required=True)
    parser.add_argument("--supplier", default=None)
    parser.add_argument("--criticality", default=None)
    parser.add_argument("--image-output", default="price_volume_scatter.png")
    parser.add_argument("--json-output", default="price_volume_scatter.json")
    args = parser.parse_args()
    main(args.filepath, args.component, args.supplier, args.criticality, args.image_output, args.json_output)
