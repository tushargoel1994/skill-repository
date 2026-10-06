---
name: solution-architect
description: stage 2 of prd-sdd pipeline. Produces solution-architecture-v[N].md and ADRs from the PRD, capability-map and tech-constraints. Use after the capability-map is reviewed and registered in the ledger, before the build-roadmap.
---

# Solution Architect — Stage 2 wrapper

A thin orchestrator. It invents no design method of its own — it delegates the thinking to the Anthropic engineering skills and maps their output into the pipeline's artifact, contract, and traceability conventions.

**1. Inputs:**
- `capability-map-v[versionNumber].md` (Stage 1) — CAP blocks and the US-### each serves.
- `prd-v[versionNumber].md` — functional and non-functional requirements, user stories (US-###) with acceptance criteria.
- Tech constraints — default: `templates/tech-constraint.md`. If the user provides a different file, use that instead. Not tracked in the ledger.
  - Hard: binding; use the named technology wherever that need arises. Not every hard constraint must be used.
  - Soft: preferences; may be overridden with a stated reason.
- `traceability-v[versionNumber].md` — read-only; used only by the pipeline gate.

**2. Uses:**
- `engineering:system-design` — engine for component structure, topology, data flow, API/data contracts, scale/reliability (its 5-step framework).
- `engineering:architecture` — engine for recording each cross-component / expensive-to-reverse choice as an ADR (its ADR format).
- No other engineering skill. Local library choices are NOT made here — they belong to Stage 3 (engineering-manager-roadmap).

**3. Process:**
1. Run `engineering:system-design` on the PRD requirements, CAP blocks and tech constraints. Derive the topology; don't assume one.
2. Fill `templates/solution-architecture.template.md` from its output. Treat NFR / cross-cutting concerns as components.
3. Keep only cross-boundary, expensive-to-reverse choices (datastores, protocols, topology, inter-component contracts). Leave local, reversible choices to Stage 3.
4. For each kept decision, run `engineering:architecture` and write the result using `templates/adr.template.md` to `adr/ADR-00X.md`. Do not alter the template's structure.
5. Surface gaps and conflicts for the user to resolve.
6. Check every CAP maps to a component and every component cites a US-### or an INFRA-## id. Define INFRA-## ids here only, on cross-cutting/NFR components that serve no story.
7. Set every new ADR Status to Proposed. The user changes it to Accepted or Rejected.

**4. Outputs**
- `solution-architecture-v[versionNumber].md` (text-first; diagram is a view).
- `adr/ADR-00X.md` — one per cross-component decision.

**5. Templates/files:** 
Writes from `templates/solution-architecture.template.md` and `templates/adr.template.md`.

---
## Pipeline gate
- **Before starting:** run `traceability-ledger` "Stage check mode" on the PRD and capability-map (Stage 1). If any fails, stop and ask the user to run `traceability-ledger` first.
- **Datetime:** set the `Datetime` header on the solution-architecture and each ADR on write.
- **On finishing:** ask the user to review the architecture, accept or reject each ADR, then run `traceability-ledger`. Do not edit the ledger.
