---
name: intent-composer
description: Stage 4 of prd-sdd pipeline. Produces one SDD intent per build-roadmap step. Use after the build-roadmap is reviewed and the traceability gate passes, or when asked to create intents.
---

# Intent Composer (Stage 4)

## Input
- `build-roadmap-v[versionNumber].md`
- `solution-architecture-v[versionNumber].md` and `adr/`
- `prd-v[versionNumber].md` (section 5a)
- `traceability-v[versionNumber].md` (gate passed)

## Uses
None. Composition only.

## Process
1. Confirm the pipeline gate passed (see below). Stop if not.
2. Write one intent per roadmap step (S##), in step order, using `templates/intent.template.md`. Skip anything not in the roadmap.
3. Take content only from these sources:
   - **Story:** the parent story from the PRD. For a split child, note which part this step delivers. For an INFRA step, state the enabler's purpose and what it unblocks.
   - **Component and contract:** copy only what this step implements from the architecture. Reference other components by id.
   - **Libraries, step number, dependencies:** from the roadmap. Express Depends-on as intent ids.
   - **Acceptance criteria:**
     - Split story: use the roadmap's "Split-story criteria allocation" for this step, unchanged. If missing or unclear, stop and send the user back to the roadmap skill.
     - Unsplit story: use the PRD 5a criteria unchanged.
     - INFRA step: use the test gate only.
     - Always add the step's EM-tier test gate, including manual checks.
4. Name files `intent-S##.md`. Optionally append the story id: `intent-S##-US-###.md`. Use one style per project.
5. Write intents to `intents/`; create the folder if missing.

## Outputs
`intents/intent-S##[-US-###].md`, one per build step.

## Content rules
Each intent must be readable on its own; developers may have only this file.
- Use bullets. One fact per bullet.
- Put open questions only at the end of the intent. Do not ask them in chat.
- Exclude:
  - schema or architecture of other components
  - vision, PRD background or ADR debate (cite the ADR id only)
  - implementation code or file-level design
  - criteria for other steps, or re-interpreted criteria
  - roadmap-wide open items and resolved decisions
  - status, GitHub links or progress tracking

---
## Pipeline gate
- **Before starting:** run `traceability-ledger` "Stage check mode" on the PRD, the solution-architecture with `adr/` (Stage 2) and the build-roadmap (Stage 3). The Gate row must also be ticked, with Last executed later than the build-roadmap's datetime. If any fails, stop and ask the user to run `traceability-ledger` first.
- **Datetime:** set the `Datetime` header on every intent on write.
- **On finishing:** ask the user to review the intents, then run `traceability-ledger`. Do not edit the ledger.
