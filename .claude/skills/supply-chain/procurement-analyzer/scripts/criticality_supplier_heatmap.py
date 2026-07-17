import argparse
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import commons

MIN_SHARE_PCT = 10.0
STRATEGIC_PCT = 25.0
MAJOR_PCT = 10.0


def criticality_spend_and_share(d: pd.DataFrame):
    """Pivot of supplier spend by criticality, plus each supplier's % share of
    spend within each criticality column (columns sum to 100)."""
    pivot = d.pivot_table(
        index="supplier_name", columns="component_criticality",
        values="line_spend_usd", aggfunc="sum", fill_value=0,
    )
    share = pivot.div(pivot.sum(axis=0), axis=1) * 100
    return pivot, share


def build_heatmap_pivot(pivot: pd.DataFrame, share: pd.DataFrame,
                         min_share_pct: float = MIN_SHARE_PCT) -> pd.DataFrame:
    """Keep suppliers with >= min_share_pct share in at least one criticality
    category; roll everyone else up into a single 'Others' row."""
    qualifying = share.index[(share >= min_share_pct).any(axis=1)]
    others = pivot.index.difference(qualifying)

    display_pivot = pivot.loc[qualifying].copy()
    if len(others) > 0:
        display_pivot.loc["Others"] = pivot.loc[others].sum()
    return display_pivot


def plot_criticality_supplier_heatmap(display_pivot: pd.DataFrame, label: str,
                                       output_path: str = "criticality_supplier_heatmap.png") -> str:
    fig, ax = plt.subplots(figsize=(10, max(6, len(display_pivot) * 0.4)))
    ax.set_title(f"Supplier × Criticality Spend Heatmap — {label}")
    sns.heatmap(display_pivot, annot=True, fmt=".0f", cmap="Blues", ax=ax)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close(fig)
    return output_path


def qualifying_tiers_for_supplier(share_row: pd.Series, threshold_pct: float) -> list:
    """share_row: share.loc[supplier] (index=criticality levels, values=share%).
    Returns qualifying tiers at/above threshold_pct, richest share first."""
    qualifying = share_row[share_row >= threshold_pct].sort_values(ascending=False)
    return [{"component_criticality": idx, "share_pct": round(float(v), 2)} for idx, v in qualifying.items()]


def build_component_breakdown(pivot: pd.DataFrame) -> list:
    """One row per supplier: total spend across all criticality tiers in this
    component (supplier axis, since --component is already fixed by the
    required filter)."""
    totals = pivot.sum(axis=1).round(2).sort_values(ascending=False)
    return [{"supplier_name": s, "total_spend": float(v)} for s, v in totals.items()]


def build_criticality_breakdown(pivot: pd.DataFrame, share: pd.DataFrame) -> list:
    """One row per (supplier_name, component_criticality): the same spend/share
    data underlying the heatmap image and `segments` below, in long form."""
    long = pivot.stack().rename("spend").reset_index()
    long = long.merge(
        share.stack().rename("share_pct").reset_index(),
        on=["supplier_name", "component_criticality"],
    )
    return long.round(2).sort_values("spend", ascending=False).to_dict(orient="records")


def segment_suppliers_by_criticality(share: pd.DataFrame, strategic_pct: float = STRATEGIC_PCT,
                                      major_pct: float = MAJOR_PCT) -> dict:
    """Bucket suppliers by their highest share of spend in any single
    criticality category:
      - strategic_suppliers: share >= strategic_pct in any category
      - major_suppliers:     share >= major_pct (but < strategic_pct) in any category
      - smaller_suppliers:   share < major_pct in every category

    strategic_suppliers/major_suppliers entries include which criticality
    tier(s) triggered the classification and at what share% — a supplier can
    cross the threshold off very few POs if that tier's total spend is small,
    so the tier detail lets a consumer sanity-check the label (see
    supplier_scorecard's po_count/n_projects for that check).
    """
    max_share = share.max(axis=1)

    strategic_names = sorted(max_share[max_share >= strategic_pct].index)
    major_names = sorted(max_share[(max_share >= major_pct) & (max_share < strategic_pct)].index)
    smaller_names = sorted(max_share[max_share < major_pct].index)

    strategic = [
        {"supplier_name": s, "qualifying_tiers": qualifying_tiers_for_supplier(share.loc[s], strategic_pct)}
        for s in strategic_names
    ]
    major = [
        {"supplier_name": s, "qualifying_tiers": qualifying_tiers_for_supplier(share.loc[s], major_pct)}
        for s in major_names
    ]

    return {
        "strategic_suppliers": strategic,
        "major_suppliers": major,
        "smaller_suppliers": smaller_names,
    }


def export_criticality_supplier_segments(payload: dict,
                                          output_path: str = "criticality_supplier_segments.json") -> str:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))
    return str(path)


def main(file_path, component_name, supplier_name=None, criticality_name=None,
         image_output="criticality_supplier_heatmap.png",
         json_output="criticality_supplier_segments.json") -> None:
    """Read the file, save the criticality x supplier heatmap image, and export
    the criticality-based supplier segmentation as JSON."""
    df = commons.load_dataset(file_path)
    commons.validate_filters(df, component=component_name, supplier=supplier_name, criticality=criticality_name)
    d = commons.filter_dataset(df, component=component_name, supplier=supplier_name, criticality=criticality_name)
    label = commons.describe_filters(component_name, supplier_name, criticality_name)

    if d["component_criticality"].dropna().empty:
        print(f"No 'component_criticality' values found for '{label}'; cannot build heatmap.")
        return

    pivot, share = criticality_spend_and_share(d)
    display_pivot = build_heatmap_pivot(pivot, share)
    saved_image = plot_criticality_supplier_heatmap(display_pivot, label, image_output)
    print(f"Heatmap saved to: {saved_image}")

    component_breakdown = build_component_breakdown(pivot)
    criticality_breakdown = build_criticality_breakdown(pivot, share)
    segments = segment_suppliers_by_criticality(share)
    filters = commons.filters_dict(component_name, supplier_name, criticality_name)
    payload = {
        "filters": filters,
        "component_breakdown": component_breakdown,
        "criticality_breakdown": criticality_breakdown,
        "segments": segments,
    }
    saved_json = export_criticality_supplier_segments(payload, json_output)
    print(f"Supplier segments written to: {saved_json}")
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--filepath", required=True)
    parser.add_argument("--component", required=True)
    parser.add_argument("--supplier", default=None)
    parser.add_argument("--criticality", default=None)
    parser.add_argument("--image-output", default="criticality_supplier_heatmap.png")
    parser.add_argument("--json-output", default="criticality_supplier_segments.json")
    args = parser.parse_args()
    main(args.filepath, args.component, args.supplier, args.criticality, args.image_output, args.json_output)
