# Procurement Analyzer — Candidate Use Cases

Real-world procurement scenarios for exercising the `procurement-analyzer` skill against `supplier-stability-dataset.csv` (517 orders, 44 suppliers, 6 component categories, 3 criticality tiers, spanning 2024–2026 across multiple projects and quarters). Each one is deliberately more than a single-script lookup — it requires combining several operations and cross-checking results against each other.

## 1. Annual supplier-base rationalization ahead of budget planning

44 active suppliers spread across 6 categories is a lot of relationships to manage, audit, and negotiate with. Before the next fiscal year, cut the tail down without touching anyone who's actually load-bearing.

- **Operations involved:** Supplier Relationship (Price vs. Volume, op 3) → Sub Category Level Supplier Division (op 2) → Supplier Ranking and Scorecard (op 7) — the "Reduce Number of Suppliers" playbook, run *per category*.
- **Why it's complex:** Six separate per-category results need to be reconciled into one consolidated exit list. A supplier that looks like a safe cut in one category can turn out to be a Critical-tier single point of failure once the heatmap is checked — the same trap Badlands/Horizon fell into during the Electrical/Standard review.

## 2. Single-source risk audit for Critical-tier components before a new program kicks off

Before committing a new project to this supply base: is any Critical-tier component category dangerously dependent on one supplier?

- **Operations involved:** Sub Category Level Supplier Division (op 2, scoped to Critical) across all 6 categories → Supplier Component/Criticality Share Breakdown (op 9) for every flagged supplier → Supplier Ranking and Scorecard (op 7) to vet 2–3 qualified alternates on delivery/defect history.
- **Why it's complex:** Inherently multi-category and multi-stage — it's a full single-source risk register, not a one-off lookup, and every flagged dominant supplier needs its own replacement-candidate shortlist (as done for Horizon → Keystone Bearing Systems in Hydraulic/Critical).

## 3. Contract renewal & negotiation prep for the top 10 suppliers by spend

Renewal season — build a data-backed negotiating position for each of the biggest suppliers: are they priced fairly vs. peers, is that gap widening or stable over time, and has their delivery/quality performance earned them anything better than "hold the line" on price?

- **Operations involved:** Supplier Summary (op 8) → Supplier Ranking and Scorecard (op 7) → Supplier Price Trend vs. Peers (op 11) — repeated across all 10 suppliers, then synthesized into per-supplier asks.
- **Why it's complex:** Same three-operation combination run 10 times over, each producing a different verdict — some suppliers get pushed on price, some on SLA terms, a few just get renewed as-is. Requires holding 10 parallel analyses in view at once.

## 4. Project-level schedule slippage root cause

A specific `project_number` is running behind schedule — is it a procurement problem, and if so, where exactly?

- **Operations involved:** Supplier Project/Component Matrix (op 10, scoped to the project) → Request Commit Received Gaps (op 6, scoped to the project) → Defect Root-Cause and Schedule Impact (op 5, project-level breakdown).
- **Why it's complex:** A diagnostic exercise, not a scorecard pull — the goal is to isolate *which* supplier/component within the project is actually responsible for the delay, versus a project-wide pattern spread across everyone involved.

## 5. Cross-category cost-creep audit under budget pressure

Finance wants a cost-reduction target list — where has unit pricing drifted up over the last 18–24 months, and is it worth pushing back on?

- **Operations involved:** Purchase Trends (op 4) across all 6 categories → Supplier Price Trend vs. Peers (op 11) for every category showing creep → Supplier Ranking and Scorecard (op 7, `--startdate`/`--enddate` scoped) to quantify dollar exposure per flagged supplier.
- **Why it's complex:** Requires distinguishing market-wide price movement (nothing actionable) from supplier-specific creep (a real negotiation target), then translating the flagged cases into an actual dollar figure using a date-scoped scorecard.
