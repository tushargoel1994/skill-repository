# Build Roadmap — [Product/feature-Name] - v[VersionNumber]

> Stage: 3 :: Detailed Engineering Build Roadmap 
> product: [product/Feature Name]
> product-version: [Version Number]
> Author: engineering-manager-roadmap
> Datetime: [YYYY-MM-DD HH:MM]


## Summary
- **Steps:** [n] across [m] milestones
- **ADR check:** [all Accepted/Rejected / blocked: list]
- **Ordering / Allocation checks:** [Pass / Fail] / [Pass / Fail / N/A]
- **Open items for you:** [n]

## Libraries & tooling
[One row per component. Local, reversible choices only. Ownership test: must NOT cross a component contract.]

| Component | Library / tool | Purpose |
|-----------|----------------|---------|
| CMP-0X | [web framework, ORM, test runner...] | [why it is needed] |

## Build sequence
Ordered by US-### Depends-On (topological). No step may depend on a later one.

| Step | Title | US-### | Component | Libraries | Depends on |
|------|-------|--------|-----------|-----------|------------|
| S01 | [short step title] | US-00X or INFRA-0X | CMP-0X | ... | None |

## EM-tier test gates
[One block per step, same S## order. Every bullet is binary pass/fail. Bullets verify the step's allocated criteria first, then engineering-only checks. Mark checks that cannot be automated as (manual).]

### S01 — [short step title]
- [Criterion check: observable outcome, e.g. "POST /x with valid body returns 201"]
- [Criterion check: ...]
- [Engineering check: e.g. "Unit coverage on module Y ≥ 80%"]
- [Engineering check: e.g. "Migration applies and rolls back cleanly"]
- (manual) [Check that cannot be automated]

## Split-story criteria allocation
[Only for split stories; otherwise write "No split stories." Rules are in the skill.]

### US-00X (parent) → US-00Xa, US-00Xb
| Parent criterion | Child step | Criterion for that step | Inherited / Sub-criterion |
|------------------|------------|-------------------------|---------------------------|
| AC-1: [PRD text] | US-00Xa (Step n) | [text] | Inherited |
| AC-2: [PRD text] | US-00Xa (Step n) | [narrower text] | Sub-criterion (AC-2.a) |
| AC-2: [PRD text] | US-00Xb (Step m) | [narrower text, closes AC-2] | Sub-criterion (AC-2.b) |

## Milestones
[One pass/fail check per bullet: cross-step integration checks only; step gates are not repeated.]

| Milestone | Steps | Done when (EM-tier gate) |
|-----------|-------|--------------------------|
| M1 — [name] | S01–S03 | • [check 1]<br>• [check 2]<br>• [check 3] |

## Ordering check
[Pass if every step's dependencies have a lower step number.]

- **Violations:** [none / list steps]
- **Overall:** [Pass / Fail]

## Allocation check
[One bullet group per split story. If none, write "No split stories."]

**US-00X → US-00Xa, US-00Xb**
- Parent criteria: [n]
- Covered by children: [n of n]
- Dropped or weakened: [none / list]
- Result: [Pass / Fail]

**Overall:** [Pass / Fail]

## Open items for you
[Only real blockers or choices. Do not ask what has a clear default. One block per question: question, options as bullets, then recommendation. If none, write "None."]

### Q1. [Question, one line]
- **Context:** [one line: why it matters, which step or story it affects]
- **Options:**
  - **A.** [option] — [one-line trade-off]
  - **B.** [option] — [one-line trade-off]
  - **C.** [option] — [one-line trade-off]
- **Recommendation:** [A / B / C] — [one-line reason]
