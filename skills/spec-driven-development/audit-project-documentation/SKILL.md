---
name: audit-project-documentation
description: Runs a project-wide documentation audit against docs/guidelines/documentation-guidelines.md — fixes what it can, notes assumptions on judgment calls, reports the rest. Use only when explicitly asked for a documentation audit (e.g. "audit the docs", "check docs against code project-wide"). Never invoke automatically or as part of execute-plan.
metadata:
  author: Tushar Goel
  version: "1.0"
---

## Role
A retrospective, whole-codebase sweep — the opposite of execute-plan's per-change, in-scope documentation. There's no plan.md here; the code itself is the source of truth for what docs should say. `specs/**` (intent.md, spec.md, plan.md, plan-review.md, implementation-notes.md) is a different lifecycle and stays untouched.

## Process

**1. Establish scope.**
- Read docs/guidelines/documentation-guidelines.md.
- Read ARCHITECTURE.md to identify module boundaries.

**2. Audit each module.**
- Parallel subagents are fine, one per module.
- Fix directly: missing/stale docstrings, JSDoc, READMEs, schema descriptions — anything the guidelines cover.
- For judgment calls (CHANGELOG-worthy? needs its own ARCHITECTURE.md section?): make the call, note the assumption. Don't stop to ask.
- Skip only if a fix would be destructive with genuinely unclear intent — flag those instead.

**3. Consolidate project-level files.**
- ARCHITECTURE.md, CLAUDE.md, root CHANGELOG.md get one pass after modules report back — not concurrent per-module edits.
- Resolves conflicts and keeps judgment calls consistent across modules.

**4. Write the audit report.**
- `docs/audits/<date>-audit.md`.
- Cover: what was fixed, what was assumed and why, what's unresolved and needs a human decision.

## NOTE
- `specs/**` is read-only, always — a project-wide sweep is not license to touch the planning chain.
- Don't backfill CLAUDE.md's "gets it wrong twice" entries — that depends on live development history this skill can't reconstruct; it's execute-plan's job going forward.
- Fix first, report second — the audit file is a record of what happened, not a task list waiting on a human.

## Output
Documentation fixed across the codebase per the guidelines; `docs/audits/<date>-audit.md` written; `specs/**` untouched.