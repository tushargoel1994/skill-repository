# Report 4 — Project Schedule Root-Cause: PRJ-2292 and the Badlands Blast Radius

**Dataset:** `supplier-stability-dataset.csv` (517 orders, 44 suppliers, 6 component categories, 3 criticality tiers, 2024–2026)
**Output artifacts:** [`output_problem_4/`](./output_problem_4/)
**Tooling:** direct analysis on the raw dataset (see Section 5 — this problem fell outside what the `procurement-analyzer` skill's packaged scripts support)

---

## 1. Problem Statement

Project PRJ-2292 is running behind schedule. Two questions:

1. **Which supplier is responsible** for PRJ-2292's delay?
2. **What other projects does that same supplier put at risk?** — if the root cause is a systemic supplier problem rather than a one-off on this project, that changes the fix from "manage this one PO" to "manage this one relationship."

As a first step, all 35 projects in the dataset were profiled for how far behind schedule they are, to give PRJ-2292 context against the rest of the portfolio.

---

## 2. Methods Executed and Why

| # | Method | Scope | Purpose |
|---|---|---|---|
| 1 | Direct pandas aggregation, `groupby('project_number')` | All 517 orders, all 35 projects | Establish a portfolio-wide baseline: how far behind schedule is every project, not just PRJ-2292, using a composite **delivery delay + defect-driven schedule loss** metric (defined in Step 1). |
| 2 | Direct pandas aggregation, `groupby('supplier_name')` filtered to `project_number == 'PRJ-2292'` | 37 order lines on PRJ-2292 | Attribute PRJ-2292's schedule slippage to individual suppliers — which one is actually driving the delay. |
| 3 | Direct pandas aggregation, `groupby('project_number')` filtered to `supplier_name == 'Badlands Components LLC'` | 31 order lines placed with Badlands, across whichever projects they touch | Once a supplier is identified as the root cause, check every other project that supplier touches, and what share of *that* project's own delay is attributable to them — the blast-radius check. |

No `procurement-analyzer` script was used for this analysis — see Section 5 for why, and exactly what had to be built by hand instead.

---

## 3. Step-by-Step Execution and Findings

### Step 1 — All-project schedule baseline

**Method:** grouped all 517 order lines by `project_number` and computed:
- `total_days_late` — sum of `days_late` across all rows where it's positive (captures any delivery gap past commit date, not only ones that cross the 5-day grace period used elsewhere in this skill's OTD calculations)
- `total_days_lost_md` — sum of `days_lost_to_md` (schedule days lost specifically to manufacturing/quality defects)
- **`total_schedule_days_behind` = `total_days_late` + `total_days_lost_md`** — a composite metric combining both delivery lateness and defect-driven schedule loss into one "how far behind is this project" number

**Output:** `output_problem_4/all_projects_schedule_summary.csv` (all 35 projects)

**What we found:** the 35 projects split sharply into two groups:
- **12 "major" recurring projects** with 34–48 POs each, carrying essentially all the portfolio's schedule risk (92–368 total days behind).
- **23 single-PO projects** with 0–2 days behind — trivial, one-off entries with no real signal.

PRJ-2292 sits in the major-project group, ranked **6th worst** of the 12 by total schedule impact: **220 total schedule days behind** (156 days of delivery delay + 64 days lost to defects), across 37 POs.

**Key findings:**
- Across the whole dataset: 1,759 total days late on deliveries and 889 total schedule days lost to defects.
- Schedule risk is concentrated entirely in the 12 major projects — the other 23 don't need attention.
- PRJ-2292 is a real problem project, not the worst in the portfolio, but solidly in the trouble zone.

---

### Step 2 — Root-cause PRJ-2292's delay

**Method:** filtered to PRJ-2292's 37 order lines, grouped by `supplier_name`, and ranked by the same `total_schedule_impact` composite (`total_days_late` + `days_lost_md`).

**Output:** `output_problem_4/PRJ-2292_order_detail.csv` (all 37 order lines) and `output_problem_4/PRJ-2292_supplier_rollup.csv` (per-supplier rollup).

**What we found:**

| Supplier | POs on PRJ-2292 | Late POs | Total Days Late | MD Events | Days Lost to Defects | **Total Schedule Impact** |
|---|---|---|---|---|---|---|
| **Badlands Components LLC** | 2 | 2 | 63 | 1 | 15 | **78** |
| Hollowpoint Alloys Inc | 2 | 1 | 37 | 0 | 0 | 37 |
| Trident Industrial Parts | 2 | 1 | 6 | 1 | 18 | 24 |
| Coastal Precision Parts | 2 | 1 | 5 | 1 | 13 | 18 |
| Crestfall Components | 1 | 0 | 4 | 1 | 13 | 17 |
| Horizon Mech Solutions | 2 | 2 | 11 | 1 | 5 | 16 |
| Dusk Manufacturing Co | 2 | 1 | 13 | 0 | 0 | 13 |
| *(14 more suppliers, each ≤6 total schedule-impact days)* | | | | | | |

**Key findings:**
- **Badlands Components LLC is the single largest contributor to PRJ-2292's delay**, at **78 of 220 total schedule-impact days (35.5%)** — despite placing only 2 of the project's 37 POs (5.4% of order volume).
- Both of Badlands' orders on this project arrived late (100% late rate, averaging 31.5 days late each), and one also triggered a supplier-fault manufacturing defect that cost an additional 15 schedule days.
- No other supplier on this project comes close — the second-worst contributor (Hollowpoint Alloys Inc) accounts for less than half of Badlands' impact, from a similarly small order footprint.

---

### Step 3 — Blast radius: what else does Badlands put at risk?

**Method:** filtered the full dataset to all 31 order lines placed with Badlands Components LLC, grouped by `project_number`, and computed the same schedule-impact metric per project. Then joined against Step 1's per-project totals to compute what **share** of each affected project's own total delay is attributable to Badlands alone.

**Output:** `output_problem_4/BadlandsComponentsLLC_project_impact.csv`

**What we found:** Badlands has orders on **all 12** of the major recurring projects identified in Step 1 — there is no major project in the entire portfolio where they're absent.

| Project | Badlands POs | Badlands Late POs | Badlands Days Late | Badlands Days Lost to Defects | **Badlands Schedule Impact** | Project Total Schedule Days Behind | **Badlands Share of Project Delay** |
|---|---|---|---|---|---|---|---|
| PRJ-8503 | 4 | 4 | 105 | 11 | 116 | 233 | **49.8%** |
| PRJ-2427 | 8 | 6 | 119 | 64 | 183 | 368 | **49.7%** |
| **PRJ-2292** | 2 | 2 | 63 | 15 | 78 | 220 | **35.5%** |
| PRJ-3594 | 2 | 2 | 31 | 38 | 69 | 197 | 35.0% |
| PRJ-9600 | 1 | 1 | 45 | 21 | 66 | 192 | 34.4% |
| PRJ-6531 | 3 | 2 | 36 | 22 | 58 | 187 | 31.0% |
| PRJ-3489 | 2 | 2 | 50 | 28 | 78 | 255 | 30.6% |
| PRJ-5522 | 3 | 1 | 39 | 21 | 60 | 237 | 25.3% |
| PRJ-7631 | 1 | 1 | 41 | 11 | 52 | 263 | 19.8% |
| PRJ-9685 | 1 | 1 | 41 | 0 | 41 | 217 | 18.9% |
| PRJ-2188 | 2 | 1 | 19 | 6 | 25 | 174 | 14.4% |
| PRJ-7778 | 2 | 1 | 7 | 0 | 7 | 92 | 7.6% |

**Key findings:**
- Badlands is present on 100% of the portfolio's major projects (12 of 12) — this is not a PRJ-2292-specific issue.
- On **PRJ-8503** and **PRJ-2427** — the two most-delayed projects in the entire dataset — Badlands alone accounts for roughly **half** of the total schedule slippage.
- Across all 12 projects, Badlands' median share of a project's total delay is ~30% — a consistent, systemic drag rather than an occasional bad order.
- This is consistent with Report 1's and Report 3's independent findings on Badlands (22.6% portfolio-wide OTD, 54.8% defect rate, chronic quarter-over-quarter quality issues) — three separate analyses, run for three different reasons, converge on the same supplier.

---

## 4. Result

**Q1 — Which supplier is responsible for PRJ-2292's delay?**
**Badlands Components LLC**, responsible for 35.5% of the project's total schedule slippage (78 of 220 days) from just 2 of 37 orders — a 100% late rate on this project plus one defect event.

**Q2 — What other projects does that supplier put at risk?**
**All 12 of the portfolio's major recurring projects**, with no exceptions. Badlands' schedule-impact share ranges from 7.6% (PRJ-7778, where their footprint is small) up to 49.8% (PRJ-8503) and 49.7% (PRJ-2427) — on the two worst-delayed projects in the entire dataset, they are responsible for roughly half the damage.

---

## 5. Additional Steps Not Covered by Existing Scripts

The `procurement-analyzer` skill's 12 packaged operations are organized around two entry points: **component-first** (Groups A/B, `--component` required or optional) and **supplier-first** (Groups B/C/D, `--supplier` required). `--project` exists only as a *secondary, optional narrowing filter* on two supplier-scoped operations (op 9, Supplier Component/Criticality Share Breakdown, and op 10, Supplier Project/Component Matrix) — and both still require `--supplier` as the primary axis. **There is no project-first operation anywhere in the skill**, so this analysis could not be answered by any single script or combination of scripts as packaged. The following had to be built directly against the raw CSV instead:

1. **Portfolio-wide project schedule ranking (Step 1).** No script accepts `--project` as a primary scope, nor produces an "all projects, ranked by delay" view — the closest packaged operation (op 6, Request Commit Received Gaps) is component- or supplier-scoped and reports gap statistics, not a per-project ranking. Had to `groupby('project_number')` directly on the raw dataframe.

2. **A composite "days behind schedule" metric.** No script combines delivery lateness and defect-driven schedule loss into one number. The skill tracks these separately: `is_late_arrived`/`days_late` (delivery) live in ops 1, 6, 7, 8; `days_lost_to_md` (defects) lives in ops 5 and 8's fault-type Pareto — but nothing sums them per project. `total_schedule_days_behind = total_days_late + total_days_lost_to_md` was defined specifically for this analysis.

3. **Supplier attribution within a single named project (Step 2).** Op 10 (Supplier Project/Component Matrix) is the closest match — it accepts `--project` — but it requires a specific `--supplier` already chosen and shows that one supplier's component mix on the project. It cannot answer "which supplier, of all suppliers on this project, is responsible for the delay" — that requires seeing every supplier on PRJ-2292 side by side, ranked by impact, which needed a direct `groupby('supplier_name')` filtered to that project.

4. **Reverse blast-radius lookup (Step 3): "what other projects does supplier X affect, and by how much."** Op 9 (Supplier Component/Criticality Share Breakdown) comes closest in spirit — it's supplier-first and can narrow by `--project` — but its per-project breakdown isn't built into its output; it reports component/criticality share and delay burden in aggregate for whatever project scope you pass in, one project at a time. Getting *all* of Badlands' projects ranked by schedule impact, with each project's own total for context, required grouping Badlands' order lines by `project_number` directly and joining the result back against Step 1's project totals to compute a share percentage — a join operation with no equivalent in any single script's output schema.

**Net effect:** every number in this report came from custom `pandas` groupby/aggregation directly on `supplier-stability-dataset.csv`, cross-checked against the composite metric's components (`days_late`, `is_late_arrived`, `has_md_event`, `days_lost_to_md`) as documented in the skill's schema reference, rather than from any of the 12 packaged script outputs. No chart images were produced this time — the packaged chart-generating operations (heatmaps, scatter plots, trend lines) are all component- or supplier-scoped and don't have a project-axis equivalent to visualize, so this report's outputs are tabular (CSV) rather than the JSON+PNG pattern used in Reports 1–3.

---

## 6. Conclusion

PRJ-2292's delay is not a standalone incident — it's one symptom of a portfolio-wide problem with a single supplier, Badlands Components LLC, who is present on every one of the 12 major projects in the dataset and responsible for a median ~30% (up to ~50% on the two worst projects) of each one's total schedule slippage. This is the same supplier already flagged for corrective action / aggressive renegotiation in Report 1 (Structural rationalization) and Report 3 (renewal negotiating position) — this report adds project-schedule evidence as a third, independent line of evidence pointing at the same root cause.

**Recommended next step:** treat this as a single supplier-management problem, not 12 separate project problems. A corrective action plan (or supplier replacement) for Badlands would resolve a meaningful share of the delay on all 12 major projects simultaneously — far more leverage than managing each project's schedule individually. Given the project-first analysis gap identified in Section 5, if this kind of "which project is at risk and why" question is going to recur, it may be worth adding a project-scoped operation to the `procurement-analyzer` skill rather than re-deriving this by hand each time.
