"""Supplier-level summary: portfolio breadth, pricing vs. peers, delivery
reliability, and quality — adapted from the tabular/summary sections of
datasets/1-supplier-stability-dateset-for-procurement/scripts/supplier_report.py
(print_summary_tile, show_supplier_scorecard, plot_share_of_category,
plot_price_index_vs_peers, show_landed_cost_table, plot_fault_type_pareto,
plot_supplier_fault_split, show_open_late_orders), reworked into JSON-friendly
tables instead of matplotlib charts.
"""
import argparse
import json
from pathlib import Path

import pandas as pd
import commons

DOMINANCE_THRESHOLD_PCT = 25.0


def compute_overall_summary(d: pd.DataFrame) -> dict:
    """Headline stats for the supplier across the filtered scope."""
    total_spend = d["line_spend_usd"].sum()
    ontime_pct = (1 - d["is_late_arrived"].fillna(False).mean()) * 100
    md_rate = d["has_md_event"].fillna(False).mean() * 100
    first_po = d["order_date"].min()
    last_po = d["order_date"].max()

    return {
        "total_spend": round(float(total_spend), 2),
        "po_count": int(len(d)),
        "components_served": int(d["component_category"].nunique()),
        "projects_touched": int(d["project_number"].nunique()),
        "first_po_date": first_po.date().isoformat() if pd.notna(first_po) else None,
        "last_po_date": last_po.date().isoformat() if pd.notna(last_po) else None,
        "ontime_pct": round(float(ontime_pct), 2),
        "md_rate_pct": round(float(md_rate), 2),
        "total_rework_cost": round(float(d["cost_of_rework_usd"].sum()), 2),
        "days_lost_to_md": int(d["days_lost_to_md"].fillna(0).sum()),
        "open_late_pos": int(d["is_open_late"].fillna(False).sum()),
    }


def compute_category_breakdown(peer_df: pd.DataFrame, supp_df: pd.DataFrame) -> list:
    """Per-component_category: this supplier's spend/PO/pricing/delivery/quality
    profile, plus how it compares to the peer set within the same scope
    (share of category spend, price index vs. peer average unit price).
    `peer_df` is the filtered scope WITHOUT the supplier filter (the market);
    `supp_df` is the same scope WITH the supplier filter."""
    category_total = peer_df.groupby("component_category")["line_spend_usd"].sum()
    peer_total_qty = peer_df.groupby("component_category")["qty_ordered"].sum()
    peer_avg_price = category_total / peer_total_qty

    scorecard = supp_df.groupby("component_category").agg(
        po_count=("order_id", "count"),
        total_spend=("line_spend_usd", "sum"),
        total_qty=("qty_ordered", "sum"),
        otd_pct=("is_late_arrived", lambda x: (1 - x.fillna(False).mean()) * 100),
        md_rate_pct=("has_md_event", lambda x: x.fillna(False).mean() * 100),
        total_rework_cost=("cost_of_rework_usd", "sum"),
        total_days_lost_to_md=("days_lost_to_md", "sum"),
    )

    scorecard["avg_unit_price"] = scorecard["total_spend"] / scorecard["total_qty"]
    scorecard["share_of_category_spend_pct"] = (
        scorecard["total_spend"] / scorecard.index.map(category_total) * 100
    )
    scorecard["is_dominant_supplier"] = scorecard["share_of_category_spend_pct"] >= DOMINANCE_THRESHOLD_PCT
    scorecard["price_index_vs_peers_pct"] = (
        scorecard["avg_unit_price"] / scorecard.index.map(peer_avg_price) * 100
    )
    scorecard["landed_cost_per_unit"] = (
        (scorecard["total_spend"] + scorecard["total_rework_cost"]) / scorecard["total_qty"]
    )

    scorecard = scorecard.round(2).sort_values("total_spend", ascending=False)
    return json.loads(scorecard.reset_index().to_json(orient="records"))


def compute_fault_type_breakdown(d: pd.DataFrame) -> list:
    """Pareto of md_fault_type among this supplier's defect events."""
    counts = d["md_fault_type"].dropna().value_counts()
    if counts.empty:
        return []
    total = counts.sum()
    return [
        {"md_fault_type": ft, "defect_count": int(c), "pct_of_defects": round(float(c / total * 100), 2)}
        for ft, c in counts.items()
    ]


def compute_fault_attribution(d: pd.DataFrame) -> dict:
    """Split of this supplier's MD events by fault attribution."""
    events = d.dropna(subset=["is_supplier_fault"])
    if events.empty:
        return {"supplier_fault_count": 0, "not_supplier_fault_count": 0, "supplier_fault_pct": None}
    supplier_fault = int(events["is_supplier_fault"].fillna(False).sum())
    total = len(events)
    return {
        "supplier_fault_count": supplier_fault,
        "not_supplier_fault_count": total - supplier_fault,
        "supplier_fault_pct": round(supplier_fault / total * 100, 2),
    }


def compute_open_late_orders(d: pd.DataFrame) -> list:
    """Currently open, past-due POs."""
    cols = ["order_id", "component_category", "project_number", "component_criticality", "qty_ordered", "commit_date"]
    open_late = d[d["is_open_late"] == True][cols].copy()
    if open_late.empty:
        return []
    open_late["commit_date"] = open_late["commit_date"].dt.date.astype(str)
    return json.loads(open_late.to_json(orient="records"))


def print_summary(supplier_name: str, label: str, summary: dict, category_breakdown: list,
                   fault_breakdown: list, fault_attribution: dict, open_late: list) -> None:
    pd.set_option("display.width", 200)

    print()
    print("=" * 60)
    print(f"  SUPPLIER SUMMARY — {label}")
    print("=" * 60)
    print(f"  Total spend:        ${summary['total_spend']:,.0f}")
    print(f"  Number of POs:      {summary['po_count']}")
    print(f"  Components served:  {summary['components_served']}")
    print(f"  Projects touched:   {summary['projects_touched']}")
    print(f"  First PO:           {summary['first_po_date'] or 'N/A'}")
    print(f"  Last PO:            {summary['last_po_date'] or 'N/A'}")
    print(f"  On-time delivery:   {summary['ontime_pct']:.1f}%")
    print(f"  MD event rate:      {summary['md_rate_pct']:.1f}%")
    print(f"  Total rework cost:  ${summary['total_rework_cost']:,.0f}")
    print(f"  Days lost to MD:    {summary['days_lost_to_md']}")
    print(f"  Open-late POs:      {summary['open_late_pos']}")
    print("=" * 60)

    print(f"\nCategory Breakdown — {label}")
    print("-" * 100)
    print(pd.DataFrame(category_breakdown).to_string(index=False) if category_breakdown else "No component categories found.")
    print()

    print(f"Fault Type Breakdown — {label}")
    print("-" * 60)
    print(pd.DataFrame(fault_breakdown).to_string(index=False) if fault_breakdown else f"No MD events recorded for {supplier_name}.")
    print()

    print(f"Fault Attribution — {label}")
    print("-" * 60)
    print(json.dumps(fault_attribution, indent=2))
    print()

    print(f"Open Late Orders — {label}")
    print("-" * 60)
    print(pd.DataFrame(open_late).to_string(index=False) if open_late else "None.")
    print()


def main(file_path, supplier_name, component_name=None, criticality_name=None,
         output_path="supplier_summary.json") -> None:
    """Read the file, print the supplier summary, and export it as JSON."""
    df = commons.load_dataset(file_path)
    commons.validate_filters(df, component=component_name, supplier=supplier_name, criticality=criticality_name)

    peer_df = commons.filter_dataset(df, component=component_name, criticality=criticality_name)
    supp_df = commons.filter_dataset(df, component=component_name, supplier=supplier_name, criticality=criticality_name)
    label = commons.describe_filters(component_name, supplier_name, criticality_name)

    summary = compute_overall_summary(supp_df)
    category_breakdown = compute_category_breakdown(peer_df, supp_df)
    fault_breakdown = compute_fault_type_breakdown(supp_df)
    fault_attribution = compute_fault_attribution(supp_df)
    open_late = compute_open_late_orders(supp_df)

    print_summary(supplier_name, label, summary, category_breakdown, fault_breakdown, fault_attribution, open_late)

    filters = commons.filters_dict(component_name, supplier_name, criticality_name)
    payload = {
        "filters": filters,
        "summary": summary,
        "category_breakdown": category_breakdown,
        "fault_type_breakdown": fault_breakdown,
        "fault_attribution": fault_attribution,
        "open_late_orders": open_late,
    }
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2))
    print(f"Summary written to: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--filepath", required=True)
    parser.add_argument("--supplier", required=True)
    parser.add_argument("--component", default=None)
    parser.add_argument("--criticality", default=None)
    parser.add_argument("--output", default="supplier_summary.json")
    args = parser.parse_args()
    main(args.filepath, args.supplier, args.component, args.criticality, args.output)
