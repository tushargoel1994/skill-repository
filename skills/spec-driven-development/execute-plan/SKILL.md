---
name: execute-plan
description: Implements an approved plan.md with TDD, documenting code as it's written and tracking progress/divergence in implementation-notes.md. Use when asked to implement/execute a plan or begin coding after a plan is approved.
metadata:
  author: Tushar Goel
  version: "1.0"
---

IMPORTANT: First read the whole skill and create implementation-notes.md (if not present) as per directions given below.

## Role
You are the engineer implementing an approved technical plan. You are not planning or designing — plan.md and its review are already settled. Your job is disciplined execution, verified against tests at every step.

## Task
Implement the changes described in plan.md, in the order plan.md specifies, writing the test for each change before the code that makes it pass, documenting each change per docs/guidelines/documentation-guidelines.md as you write it, tracking progress and any divergence in implementation-notes.md, and verifying every change against the project's real test/build commands before moving to the next.

## Process

**0. Pre-execution check.** Run references/pre-execution-checks.md. Don't proceed until it's clean.

**1. Read context, set up notes.** Read plan.md (+ sub-task plans if split) and plan-review.md — note which Blocking findings are resolved and which Worth-considering risks were accepted. Read CLAUDE.md, ARCHITECTURE.md, and docs/guidelines/documentation-guidelines.md for conventions. Create implementation-notes.md next to the plan.md being executed if it doesn't exist (seed its Checklist from plan.md); if it exists, resume it in place.

**2. Implement test-first, in plan order.** For each change: write the test from its "Proof" → confirm it fails for the right reason → implement the minimum to pass → document per documentation-guidelines.md → run the full suite → update Checklist and Skills Used. Don't skip ahead or batch unrelated changes — the order is deliberate and you can confirm from the attached reasoning.
   - Requirement from plan.md completed -> check off in implementation-notes.md/checklist
   - Find any new command or convention in plan.md/ or you need new command/conventions -> Add to claude.md
   - Find architecture changes (File system, configs, DB changes etc) -> Log in docs/architecture/ARCHITECTURE.md
   - Require new dependencies, assets or libraries - mention in implementation-notes.md/dependencies
   - used specific skills during implementation (plan suggested or otherwise) - Note in implementation-notes.md/skills Used

**3. Handle divergence.** If real work must differ from plan.md, log it in Divergence — never edit plan.md itself. If the divergence is scope/risk-material, stop and ask before proceeding. Provide reason and details about divergence in brief.

**4. Keep living docs current.** Update ARCHITECTURE.md/CLAUDE.md for anything new (not read-only). Add a CHANGELOG.md entry if user-facing, per documentation-guidelines.md. Log any new infra/config/dependency in Dependencies.

## implementation-notes.md
One file per executed plan: `specs/<slug>/implementation-notes.md`, or per sub-task at `specs/<slug>/tasks/<sub-task-slug>/implementation-notes.md` if split (no parent rollup). Update in place across resumed runs. Sections (more may be added later):
1. **Checklist** — one line per plan.md task, checked off once implemented and verified.
2. **Divergence** — what changed from plan.md, why, and the details.
3. **Skills Used** — skill name + brief note on how it was used.
4. **Dependencies** — anything new introduced (infra/config/package) and why, even if plan.md already covers it.

Be brief and objective while writing implementation-notes.md.

## NOTE
- IMPORTANT: Never Edit or Delete intent.md, spec.md, plan.md, plan-review.md or any subtask plan.md or plan-review.md files. They are read-only to you.
- Never weaken or bypass a test to pass it, unless plan.md approved that.
- Never mark a step done without an actual passing test run.
- Step 0's smoke test isn't coverage — it only proves the runner works.
- If plan.md assumes a skill that doesn't exist, stop and ask.
- Documentation happens per-change in step 2, only for the guideline sections relevant to what changed — not a batch sweep. Whole-repo audits are a different skill's job.
- Doesn't review the final diff for security/correctness beyond passing tests — that's a separate pass.

## Output
- Code + tests, documented inline; 
- implementation-notes.md current; 
- changes to ARCHITECTURE.md/CLAUDE.md as needed

