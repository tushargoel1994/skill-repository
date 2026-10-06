---
name: traceability-ledger
description: Generates and verifies the PRD-to-SDD traceability ledger, linking each PRD story (US-###) to its capability, component and build step, and each build step to its intent, GitHub issue and status. Also keeps the run checklist other stages check before starting. Invoke when asked to create or update the ledger for a PRD, after each stage's output is reviewed, and as the hard gate before intent composition.
---

# Traceability Ledger (cross-cutting)

## Input
- `prd-v[versionNumber].md`

### Source files per column
- `capability-map-v[versionNumber].md`: Capability column
- `solution-architecture-v[versionNumber].md` and `adr/`: Component column; INFRA section (INFRA-## ids from the architecture)
- `build-roadmap-v[versionNumber].md`: Build step(s) column (story ledger) and the whole Build-step ledger (one row per step)
- `intents/intent-S##.md` (or `intents/intent-S##-US-###.md`): Intent column of the Build-step ledger
- User-supplied: Github issue links and Status

## When this skill runs
- Only this skill writes the ledger. Stage skills write their own output file, then tell the user to run this skill.
- The user reviews that output, then invokes this skill. One run per stage, after review.
- A stage's columns are **regenerated** from its source on every run, not patched.
  - Re-running after an edit or an upstream redo is normal.
  - Rows whose story or step no longer exists are removed.

## Process
1. Seed story rows from the discrete US-### stories in PRD section 5a.
2. After user review of a stage, regenerate that stage's columns from its source.
3. Stage 3 run: keep already-filled Intent, Github issue and Status values for steps whose id still exists.
4. Gate (before Stage 4): fill the first Gate check; fail loudly on any unmet item.
5. After Stage 4: fill the Intent column from `intents/` and complete the second Gate check.
6. After intents are written, ask the user for the Github issue link per intent; write them to the Github issue column. Write Status as the user reports it during SDD.
7. After every run, update the Pipeline run checklist.

## Datetime rule
Every stage output carries a `Datetime` header (`YYYY-MM-DD HH:MM`, local), set whenever the file is written or rewritten. Stage skills only set it; the format is defined here.

## Pipeline run checklist
The template's checklist is the record other stages read. On every run for a stage:
1. Take **File datetime** from the `Datetime` header of the stage's output (latest file if several). No header: do not tick; tell the user the file needs one.
2. Set **Last executed** to the current local datetime; list regenerated columns in **Ledger updated**.
3. Re-check every other row; untick any stale row and mark it stale in **Ledger updated**.

## Stage check mode (read-only)
Each stage skill calls this before starting. Writes nothing.
- Pass for an input only if its checklist row is ticked and Last executed is later than the file's current `Datetime`.
- Otherwise fail: name the input and reason, and tell the user to run this skill for that stage.
- PRD: use its `Updated Date` (or `Datetime`) header; a date alone means 00:00.

## Outputs
- `traceability-v[versionNumber].md` from `templates/traceability.template.md`, created if absent.
- Updated columns and Pipeline run checklist on every run.
