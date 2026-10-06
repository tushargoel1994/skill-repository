---
name: capability-architect
description: Stage 1 of the PRD-SDD pipeline. This skill turns a PRD into a technology-free capability map — logical architecture blocks, each traced to the story (US-### format) it serves. Invoke this skill when the user asks to create a capability-map from a PRD (Product Requirement Document).
---

# Capability Architect (Stage 1)

## Input
- `prd-v[versionNumber].md`
- `traceability-v[versionNumber].md`

**IMPORTANT**
- If the PRD or traceability file is missing, ask the user to provide it and exit.
- If either lacks the stories (US-###), tell the user and exit.

## Capability block
An isolated, functionally complete component that connects with other blocks to form the system. It can be an infrastructure piece, a functional group, a security layer, a database layer, etc.

Example: "Data ingestion from a source" is a block. It ingests data from the source and passes it to the next block.

Fields per block are defined in `templates/capability-map.template.md`.

### Rules
- Do not use any engineering skill.
- Describe function only; no technology unless the PRD states it (tag it PRE-COMMITTED).
- Functional groups that must live and move together belong in one block.
- Many-to-many between stories and blocks is allowed and expected.
- Data in -> out is a short description, no technology or schema.

## Process
1. Read the PRD and extract all stories (US-###) and requirements.
2. Group them into blocks by single responsibility.
3. For each block, fill the template fields.
4. Tag PRE-COMMITTED constraints inherited from the PRD.
5. Coverage check: every story maps to at least one block; report any uncovered story to the user.

## Output
`capability-map-v[versionNumber].md` in the PRD's folder, from `templates/capability-map.template.md`.

---
## Pipeline gate
- **Before starting:** run `traceability-ledger` "Stage check mode" on the PRD. If it fails, stop and ask the user to run `traceability-ledger` first.
- **Datetime:** set the `Datetime` header on write.
- **On finishing:** ask the user to review the capability map, then run `traceability-ledger`. Do not edit the ledger.
