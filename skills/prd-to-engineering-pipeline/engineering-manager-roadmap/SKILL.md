---
name: engineering-manager-roadmap
description: stage 3 of prd-sdd pipeline. Produces an ordered build-roadmap (build sequence, libraries, test gate per step) from the PRD and solution-architecture. Use after the solution-architecture and ADRs are reviewed and registered in the ledger, or when asked for a build roadmap.
---

# Engineering Manager — Build Roadmap (Stage 3)

## Inputs
- `prd-v[versionNumber].md`
- `solution-architecture-v[versionNumber].md`
- `adr/` — ADRs from Stage 2. The user sets each Status to Accepted or Rejected.

## Uses
- `engineering:testing-strategy` — EM-tier test gates.
- `engineering:deploy-checklist` — optional, for release gating.

## Process
1. **ADR check:** read every ADR in `adr/`. If any Status is still Proposed, stop and list them. Proceed only when all are Accepted, Rejected or Superseded. Do not build on Rejected ADRs.
2. Order US-### topologically by PRD Depends-On. Assign each build step an id `S##` in build order. A step is one self-contained, independently testable unit (downstream: one intent, one GitHub issue, one status). Enabler steps use the INFRA-## ids defined in the solution-architecture; define none here.
3. Split a story into US-###a/b when it spans more than one step. Children keep the parent ID.
4. Allocate each split story's PRD criteria (AC-1, AC-2, ...) across its children:
   - A criterion one child fully satisfies is inherited unchanged.
   - A criterion spanning children becomes one narrower sub-criterion per child (AC-1.a, AC-1.b), equivalent together to the original. The last child closes it.
   - Never copy a criterion into a child that cannot satisfy it alone.
   - Cover every parent criterion; drop or weaken none; invent none. Extra checks go in the test gate.
   - If a criterion's owner or split is unclear, ask the user.
5. Choose libraries per component. Local, reversible choices only; anything crossing a component contract belongs to the architect.
6. Write each step's test gate via `engineering:testing-strategy`. Check the step's allocated criteria first, then engineering-only checks. Mark non-automatable checks `(manual)`.
7. Run the ordering and allocation checks. Both must pass.
8. Raise open items only when there is no clear default.

## Readability rules
- No paragraphs; use tables and bullets.
- One fact or check per bullet, max ~15 words.
- Every check is pass/fail and objective (number, status, visible outcome); no vague wording.
- Bold only labels and key terms.

## Output
`build-roadmap-v[versionNumber].md` from `templates/build-roadmap.template.md`. The Split-story criteria allocation must be complete: Stage 4 copies it into intents.

> Scope: macro build order only. SDD plans (micro, PR-sized units) are produced downstream.

---
## Pipeline gate
- **Before starting:** run `traceability-ledger` "Stage check mode" on the PRD and the solution-architecture with `adr/` (Stage 2). If any fails, stop and ask the user to run `traceability-ledger` first.
- **Datetime:** set the `Datetime` header on write.
- **On finishing:** ask the user to review the roadmap, then run `traceability-ledger`. Do not edit the ledger.
