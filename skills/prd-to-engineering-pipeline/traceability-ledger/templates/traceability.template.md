# Traceability Ledger — [Product/Feature-Name]-v[VersionNumber]

> Product : [Product/Feature Name]
> Author: traceability-ledger-skill
> version: [version Number]
> Datetime: [YYYY-MM-DD HH:MM]

> Written only by the traceability-ledger skill; never hand-edited. Born at the PRD; grows each stage; HARD GATE before Stage 4; status-tracked through SDD.
> Scope: pipeline-driven LARGE work only. Ad-hoc small intents are out of scope and get no row.


## Ledger (story level)
| US-### | Title | PRD ref | Capability | Component | Build step(s) | Flags |
|--- |--- |--- |---|---|---|---|
| US-001 | ... | 5a | CAP-0X | CMP-0X | S01 | - |

A story's build steps are listed here; the step-level detail (intent, Github issue, status) lives in the Build-step ledger below.

## Build-step ledger (filled at Stage 3, intents added at Stage 4)
One row per build-roadmap step, one intent per step. Github issue and Status are tracked per step.

| Step | Title | US-### | Component | Intent | Github issue | Status | Flags |
|--- |--- |--- |---|---|---|---|---|
| S01 | ... | US-001 | CMP-0X | intent-S01 | [issue link] | [as reported by user] | - |

- Step and US-### come from the build-roadmap; a split story's children (US-###a/b) appear on separate rows.
- Github issue and Status are user-supplied and written by the ledger skill.

## INFRA (no US-### by design)
[INFRA-## ids from the solution-architecture, so they are not flagged as orphans.]

## Gate check (run before Stage 4)
- [ ] Every US-### has a complete row (capability -> component -> build step)
- [ ] Every build step appears in the Build-step ledger and maps to a US-### (or an INFRA item)
- [ ] No orphan line (behavior citing no US-###)
- [ ] No gap (capability/component with no owner)
- [ ] NFRs covered
- Result: [PASS / FAIL — counts]

## Gate check (after Stage 4, intents written)
- [ ] Every build step has exactly one intent
- Result: [PASS / FAIL — counts]

## Pipeline run checklist
Updated by traceability-ledger on every run. Ticked only when Last executed is later than File datetime; unticked when stale. For several files (ADRs, intents), File datetime is the latest.

| Done | Pipeline stage | Output file | File datetime | Ledger updated | Last executed |
|---|---|---|---|---|---|
| [ ] | PRD (seed) | prd-[name]-v[N].md | | US-###, Title, PRD ref | |
| [ ] | Stage 1: capability-architect | capability-map-v[N].md | | Capability column | |
| [ ] | Stage 2: solution-architect | solution-architecture-v[N].md, adr/ | | Component column, INFRA | |
| [ ] | Stage 3: engineering-manager-roadmap | build-roadmap-v[N].md | | Build step(s), Build-step ledger | |
| [ ] | Gate (before Stage 4) | this file | n/a | Gate check | |
| [ ] | Stage 4: intent-composer | intents/ | | Intent column | |
| [ ] | Github issues | n/a | n/a | Github issue column | |
