# Supplier Stability Dataset

Test dataset for the **procurement-analyzer** skill (`.claude/skills/supply-chain/procurement-analyzer/`).

## What this is

`raw/supplier-stability-dataset.csv` — 517 purchase orders across 44 suppliers, 6 component categories (Electrical, Hydraulic, Mechanical, Optical, Structural, Thermal Management), 3 criticality tiers (Critical, High, Standard, per component), spanning Jan 2024–Mar 2026 across 35 projects. Each row is an order line with delivery dates, defect/rework data, and pricing.

**Source:** downloaded from Kaggle — [Supplier Stability Dataset for Procurement](https://www.kaggle.com/datasets/shfarshid/supplier-stability-dataset-for-procurement).

See `report_cases.md` for the five candidate procurement scenarios this dataset was designed to exercise — each one deliberately requires chaining multiple `procurement-analyzer` operations and cross-checking results, rather than a single script lookup.

## What's been done

`output/` contains five completed analyses, each a full report plus its supporting chart/data artifacts in a matching `output_problem_N/` folder:

| Report | Question | Key finding |
|---|---|---|
| [`report_1.md`](./output/report_1.md) | Rationalize the 35-supplier Structural category into promote/renegotiate/exit buckets | 5 promote, 7 renegotiate, 6 exit; cross-category check reversed one exit decision (Western Alloy Fab, a dominant Electrical/Critical supplier) |
| [`report_2.md`](./output/report_2.md) | Is any Critical-tier category dangerously single/dual-sourced? | Electrical/Critical: Greystone Fabrications + Western Alloy Fab hold 66% combined — the only category to cross the 50% threshold |
| [`report_3.md`](./output/report_3.md) | Renewal negotiating position for the 5 largest suppliers by spend | Pricing and performance diverge in almost every direction — no supplier gets a uniform "hold the line" treatment |
| [`report_4.md`](./output/report_4.md) | Root-cause project PRJ-2292's schedule slippage | Badlands Components LLC is responsible for 35.5% of the delay, and is present on all 12 major projects in the portfolio |
| [`report_5.md`](./output/report_5.md) | Where has unit pricing drifted up in the last 18 months, and is it worth pushing back? | Category-wide trends look flat/declining, but 5 specific supplier×category relationships account for ~$775K in contestable excess cost |

Reports 1–3 and 5 ran entirely on the packaged `procurement-analyzer` scripts. Report 4 (project-first analysis) and part of report 5 (supplier×category drift screening) fell outside what the skill's 12 packaged operations support — see each report's own "Additional Steps Not Covered by Existing Scripts" section for exactly what had to be built by hand, and why. Those gaps are candidates for new operations if this kind of question recurs.

## Structure

Only `raw/` and `output/` are populated so far — `processed/` and `code/` are empty pending any cleaning/notebook work (see root `CLAUDE.md` for the full per-dataset layout convention).
