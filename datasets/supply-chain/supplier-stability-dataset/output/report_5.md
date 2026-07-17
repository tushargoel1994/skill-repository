# Report 5 — Cost-Reduction Target List: Unit Price Drift, Last 18 Months

**Dataset:** `supplier-stability-dataset.csv` (517 orders, 44 suppliers, 6 component categories, 3 criticality tiers, 2024–01 through 2026–03)
**Output artifacts:** [`output_problem_5/`](./output_problem_5/)
**Tooling:** `procurement-analyzer` skill (ops 4 and 7), plus custom analysis where the skill has no matching operation (Section 5)

---

## 1. Problem Statement

Finance wants a cost-reduction target list: where has **unit pricing drifted up** over the last 18–24 months, and **is it worth pushing back on**? "Worth pushing back" means the increase isn't explained by improved delivery/quality performance and the supplier is now priced above what peers charge for the same category — i.e., real, contestable cost creep rather than a fair price for better service.

**Time window:** the dataset spans 26 months (Jan 2024 – Mar 2026). It was split into a **baseline period (Jan–Sep 2024, 9 months)** and a **recent period (Oct 2024–Mar 2026, 18 months)** — the recent window matches the "last 18–24 months" framing, with enough baseline data (9 months / 3 quarters) to establish a real before/after comparison.

---

## 2. Methods Executed and Why

| # | Method | Scope | Purpose |
|---|---|---|---|
| 1 | `price_volume_trend.py` (op 4 — Purchase Trends) | `--component <category>`, run once per category (6x) | First pass: does *category-wide* average pricing show an upward trend? This is the skill's native tool for price-over-time. |
| 2 | Custom pandas: spend-weighted price by `(supplier_name, component_category)` × period | All 517 orders, all 44 suppliers × 6 categories (82 pairs with data in both periods) | Op 4's category-wide average turned out to hide the real signal (Step 1) — pricing moves per *supplier relationship*, not per category, and blending 5–10 suppliers together washes that out. This screens every supplier×category combination for baseline-vs-recent price drift and ranks by actual dollar impact (`excess_cost_vs_baseline`), not just percentage. |
| 3 | `supplier_scorecard.py` (op 7 — Supplier Ranking and Scorecard), scoped with `--startdate 2024-10-01` | `--supplier <name> --component <category>`, run once per high-confidence flagged pair (5x) | Was the price increase earned? Scopes delivery/defect/rework performance to *only the recent, higher-priced window* — the relevant question isn't "has this supplier ever performed well," it's "did they perform well enough during the period they charged more." |
| 4 | Custom pandas: recent-period peer price comparison | Same 5 flagged pairs, recent period only | Confirms whether the price increase pushed the supplier **above** category peers (a real market-rate problem) or merely narrowed a discount they still hold (less urgent). |

---

## 3. Step-by-Step Execution and Findings

### Step 1 — Purchase Trends per category (negative result — see why this doesn't answer the question)

**Command pattern:**
```
uv run .claude/skills/procurement-analyzer/scripts/price_volume_trend.py \
  --filepath datasets/supplier-dataset/supplier-stability-dataset.csv \
  --component "<category>" \
  --output datasets/supplier-dataset/output_problem_5/price_trend_component-<category>.png \
  --json-output datasets/supplier-dataset/output_problem_5/price_trend_component-<category>.json
```
Run once per category (6x).

**What we found:** comparing each category's baseline-period average price to its recent-period average (unweighted monthly mean, the skill's own convention for this chart), **not one category shows meaningful upward drift**:

| Category | Baseline Avg (Jan–Sep 2024) | Recent Avg (Oct 2024–Mar 2026) | Category-Wide Drift |
|---|---|---|---|
| Mechanical | $2,663.91 | $2,717.30 | +2.00% |
| Thermal Management | $3,064.47 | $3,001.81 | -2.04% |
| Hydraulic | $4,260.71 | $4,064.23 | -4.61% |
| Electrical | $7,869.80 | $7,241.55 | -7.98% |
| Structural | $1,583.54 | $1,007.56 | -36.37% |
| Optical | $29,382.75 | $17,361.59 | -40.91% |

**Key findings:**
- Category-wide, pricing is flat or declining everywhere — if this were the whole analysis, the answer to Finance would be "nothing to push back on," which would be **wrong**.
- The reason: a category blends 5–18 suppliers together. If some suppliers raise prices while others (often cheaper new entrants ramping up volume) pull the blended average down, category-level view cancels out exactly the signal Finance is asking about. This motivated Step 2.

---

### Step 2 — Supplier × category price drift screen (the real target list)

**Method:** for every `(supplier, category)` pair with at least 2 orders in *both* the baseline and recent periods (26 of 82 possible pairs qualify — the rest have too few orders in one period to trust a comparison), computed spend-weighted average unit price per period (`total_spend / total_qty`, the same convention the skill's scorecard uses) and the resulting drift.

**Output:** `output_problem_5/price_drift_screen_all_supplier_category_pairs.csv` (all 82 pairs with any data in both periods, for reference)

**What we found — high-confidence upward drift (≥2 POs each period):**

| Supplier | Category | Baseline POs / Price | Recent POs / Price | Drift | Recent Qty | **Excess Cost vs. Baseline Pricing** |
|---|---|---|---|---|---|---|
| Ironclad Assemblies | Optical | 2 / $8,574.97 | 4 / $20,221.44 | **+135.82%** | 39 | **$454,213** |
| Ironclad Assemblies | Mechanical | 5 / $1,387.79 | 3 / $3,699.80 | **+166.60%** | 46 | **$106,353** |
| Coastal Precision Parts | Thermal Management | 2 / $1,314.93 | 3 / $3,509.42 | **+166.89%** | 48 | **$105,335** |
| Zenith Alloy Solutions | Thermal Management | 4 / $2,994.61 | 2 / $5,318.55 | **+77.60%** | 24 | **$55,775** |
| Trident Industrial Parts | Mechanical | 2 / $1,806.45 | 2 / $4,212.08 | **+133.17%** | 22 | **$52,924** |

**Total excess cost, high-confidence tier: ~$774,600** — about 1.3% of total dataset spend, concentrated in just 5 relationships.

**Key findings:**
- Only 26 of 82 supplier×category pairs have enough orders (≥2 per period) to trust a drift comparison — this dataset's order volume per relationship is thin, a real constraint on confidence (see caveat below).
- Of those 26, only 5 show genuine upward drift — the rest are flat or declining, consistent with Step 1's category-level finding once you account for the fact that most relationships simply don't have enough data to move the needle either way.
- **Ironclad Assemblies appears twice** (Optical and Mechanical) — notable because Report 3 characterized Ironclad as a reliable, largely cost-competitive supplier based on whole-history pricing. This screen shows that reputation may already be dated in 2 of its 6 categories.

---

### Step 3 — Is it worth pushing back? (recent performance + peer-price check)

**Command pattern:**
```
uv run .claude/skills/procurement-analyzer/scripts/supplier_scorecard.py \
  --filepath datasets/supplier-dataset/supplier-stability-dataset.csv \
  --supplier "<name>" --component "<category>" --startdate 2024-10-01 \
  --output datasets/supplier-dataset/output_problem_5/scorecard_recent_<Supplier>_<Category>.json
```
Run once per flagged pair (5x), scoped to the recent (higher-priced) window only.

**What we found:**

| Supplier / Category | Recent OTD | Recent Defect Rate | Recent Rework % | Recent Price vs. Category Peers |
|---|---|---|---|---|
| Ironclad Assemblies / Optical | 100.00% | 0.00% | 0.00% | **118.66%** (18.7% above peers) |
| Ironclad Assemblies / Mechanical | 100.00% | 0.00% | 0.00% | **133.64%** (33.6% above peers) |
| Coastal Precision Parts / Thermal Mgmt | **66.67%** | **33.33%** | 3.05% | **117.56%** (17.6% above peers) |
| Zenith Alloy Solutions / Thermal Mgmt | 100.00% | 0.00% | 0.00% | **179.99%** (80% above peers) |
| Trident Industrial Parts / Mechanical | **50.00%** | 0.00% | 0.00% | **151.34%** (51.3% above peers) |

**Key findings:**
- **All 5** flagged relationships are now priced *above* category peers in the recent window — the drift didn't just move pricing up in isolation, it pushed every one of them out of competitive range.
- **Coastal Precision Parts and Trident Industrial Parts got worse, not better**, during the very window they charged more (66.7% OTD / 33.3% defects, and 50% OTD / 10-day average lateness, respectively) — the clearest possible case for pushing back.
- **Ironclad Assemblies and Zenith Alloy Solutions** delivered flawlessly during the recent window (100% OTD, 0% defects both) — the price increase isn't covering a service failure, but flawless performance doesn't automatically justify a 19–80% premium over peers who are presumably also delivering acceptably. This is a "renegotiate from strength" situation, not a "reward" situation.

---

## 4. Result: Cost-Reduction Target List

| Priority | Supplier / Category | Drift | Excess Cost | Now vs. Peers | Performance Justification? | **Verdict** |
|---|---|---|---|---|---|---|
| 1 | Coastal Precision Parts / Thermal Management | +166.9% | $105,335 | +17.6% | **None** — performance *declined* (66.7% OTD, 33.3% defects) | **Push back hard.** Paying more for worse service; no defense available. |
| 2 | Trident Industrial Parts / Mechanical | +133.2% | $52,924 | +51.3% | **None** — 50% OTD, 10-day avg lateness | **Push back hard.** Largest peer-relative premium in the list, delivery got worse. Consistent with Trident's chronic OTD problems flagged in Reports 1 and 2 (Structural/Critical). |
| 3 | Ironclad Assemblies / Optical | +135.8% | $454,213 | +18.7% | Partial — flawless delivery, but doesn't justify the size of the jump | **Push back, moderate leverage.** Largest dollar exposure by far; negotiate from a position of a strong overall relationship, not an adversarial one. |
| 4 | Ironclad Assemblies / Mechanical | +166.6% | $106,353 | +33.6% | Partial — flawless delivery, same caveat as above | **Push back.** Second Ironclad category on this list — worth raising both together at renewal rather than separately. |
| 5 | Zenith Alloy Solutions / Thermal Management | +77.6% | $55,775 | +80.0% | Partial — flawless delivery, but 80% above peers is hard to defend on quality alone | **Push back, but low priority.** Smallest category for Zenith (3% of their portfolio) — worth a conversation, not worth risking the (much larger, well-performing) Electrical relationship over. |

**Total addressable excess cost across this list: ~$774,600** (recent 18-month window; recurring annually if left unaddressed).

**Lower-confidence candidates flagged for verification, not fully vetted (thin baseline sample, 1 PO):** Badlands Components LLC / Optical stands out even in this weaker tier — $862,907 in apparent excess cost — and given Badlands' already well-documented chronic delivery/quality failures (Reports 1, 3, and 4), it's worth a manual pull of the underlying POs before treating the number as solid, rather than dismissing it outright. Other 1-PO-baseline candidates (Riverton Manufacturing/Thermal Mgmt, Stratos Machined Parts/Hydraulic and /Electrical, Horizon Mech Solutions/Hydraulic — full list in the CSV) show drifts too large (up to +1,012%) to be believable as pricing trends; they're far more likely single large/small-order artifacts and should be data-quality-checked, not acted on.

---

## 5. Additional Steps Not Covered by Existing Scripts

As with Report 4, the question as Finance framed it doesn't map onto any single packaged operation:

1. **No operation screens the full supplier × category matrix for price drift ranked by dollar impact.** Op 4 (Purchase Trends) is the skill's price-over-time tool, but it's category-scoped and averages across every supplier in that category — which Step 1 showed actively hides the signal Finance is asking about. Op 11 (Supplier Price Trend vs. Peers) is supplier-scoped and *does* compare against peers, but it has to be run one supplier at a time and doesn't rank or screen — you'd have to already suspect a specific supplier before running it. Getting from "44 suppliers × 6 categories" down to "these 5 matter" required a custom pandas screen with no equivalent packaged script.

2. **No operation computes a baseline-vs-recent-period comparison at all.** Every trend-related operation in the skill (ops 4 and 11) reports a continuous monthly series; turning that into a "before 18 months ago" vs. "after" split, and a dollar-denominated `excess_cost_vs_baseline` metric, had to be built by hand.

3. **No operation scopes a scorecard to *just the recent window* while also filtering to one supplier–category pair.** Op 7 does support `--startdate`, which made Step 3 possible without custom code — this is the one part of this report where the packaged tooling covered the need directly. The recent-period peer-price comparison in Step 3, however, again had no built-in equivalent (op 8's `price_index_vs_peers_pct` is whole-history only) and was computed directly against the raw CSV.

**Net effect:** Steps 1 and 3's scorecard portion used the packaged skill as-is; Step 2 (the core screening logic) and half of Step 3 (recent-period peer pricing) required direct `pandas` work against `supplier-stability-dataset.csv`. If "where has pricing drifted and is it above peers" is a recurring Finance question — which this report suggests it is, since the category-level tool alone would have produced a false "nothing to see here" — a dedicated operation (supplier×category drift screen with a configurable baseline/recent split, ranked by dollar impact) would be a stronger candidate for the skill than the project-schedule operation flagged in Report 4.

---

## 6. Conclusion

The category-level view Finance would naturally reach for first (op 4, Purchase Trends) says pricing is flat-to-declining across the board — and that answer is wrong. The real story only appears at the supplier × category level, where 5 specific relationships account for roughly $775K in excess cost over the recent 18 months, all now priced above their category peers, and two of them (Coastal Precision Parts, Trident Industrial Parts) got *worse* on delivery during the exact window they raised prices — the clearest possible negotiating position.

**Recommended action:**
1. Lead renewal conversations with **Coastal Precision Parts** and **Trident Industrial Parts** — price increases with no performance justification, backed by hard numbers.
2. Raise both **Ironclad Assemblies** categories (Optical, Mechanical) together — largest dollar exposure on the list, but from a position of a genuinely strong relationship, so frame as "bring this back toward peer pricing" rather than a threat.
3. Treat **Zenith Alloy Solutions**/Thermal Management as a lower-priority, opportunistic ask — not worth spending relationship capital on given it's a small slice of a supplier whose flagship (Electrical) relationship remains highly valuable (Report 3).
4. Before acting on it, verify the **Badlands Components LLC / Optical** $863K figure with underlying PO detail — the dollar magnitude and the supplier's independently well-documented track record both argue it's real, but the 1-order baseline sample means it needs a manual check rather than automatic inclusion in the target list.
