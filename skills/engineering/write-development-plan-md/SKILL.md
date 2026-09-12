---
name: write-development-plan-md
description: This skill is used to create one or more detailed technical plan(s) for the implementation provided in spec.md file. Use this when user asks to create plan from spec.md (specification file)
metadata:
  author: Tushar Goel
  version: "1.0"
---

## Role
You are the lead engineer of this project and have complete visibility on the technical implementation of this project.

## Task
Your role is to create the technical implementation plan from the provided spec.md file. The plan should be direct and well detailed — enough depth that a new developer who has never seen the codebase can read the plan and implement the changes with ease.

## Process
1. This skill assumes the session is already running in Claude Code plan mode. If it isn't, treat "do not edit any file" (see NOTE) as a hard rule regardless — plan mode's own edit-blocking is not something this skill can turn on from within a prompt.
2. Read intent.md, spec.md, docs/architecture/ARCHITECTURE.md, and CLAUDE.md. Get an overview of what to implement, the current state of the project, and the team's stated conventions. Also check current dependencies.
3. Verify the instructions from spec.md against the real codebase — confirm the references exist and match what's described. If there's a discrepancy, highlight it rather than moving forward silently.
4. Note down each change spec.md is suggesting, including additional implementation dimensions it didn't consider. IMPORTANT: spec.md tells you what's required; actual implementation can and will contain additional dimensions spec.md didn't anticipate. It's your responsibility to catch these. Mark any addition beyond spec.md's stated scope distinctly, so it's visible to whoever reviews the plan that scope changed. If spec.md itself asks you to ignore something, note that at the bottom and say why that functionality isn't there.
5. For anything unclear or ambiguous — in spec.md, in the codebase, or in how to proceed — ask the user directly in chat rather than guessing. When you ask, present the real options with their tradeoffs, and give your own recommendation with a reason. Do this before finalizing the plan, not after.
6. Resolve every question spec.md left for engineering. Map the files that need to be edited, libraries or dependencies that need to be installed, and the code that needs to be implemented.
7. Decide whether this stays a single plan or should be split into multiple sub-tasks. Consider that during actual implementation, a single agent given too much work can fill its context window fast, and that each sub-task will likely become its own GitHub issue.
   - If it stays single: continue with one plan.md.
   - If it splits: write a short top-level plan.md (the split decision, the reasoning, links to each sub-task), and give each sub-task its own folder at specs/[issue-number]-[issue-info]/tasks/[sub-task-number]-[sub-task-slug]/, each with its own plan.md.
8. Check which of the following skills will be in use during the code implementation phase (none has been implemented at this stage — this step is currently a no-op, kept as a forward stub):
   - low-level-design-skill (defines the design principle for each implementation)
   - infrastructure-implementation-skill (used if new infrastructure has to be created for the functionality)
   *More skills will be envisioned in the future.
9. For each task/subtask, define the following:
   - Change to be made
   - Order of change
   - Risks associated with the change
   - Proof (test/verification that shows the change worked)
10. Write a detailed draft of plan.md (or of each sub-task's plan.md, if split). Then invoke the implementation-plan-critic subagent — once — providing intent.md, spec.md, the plan.md being reviewed, and (if split) the sibling sub-task plans as context so it can check for conflicts between them. Point it at the folder these files are stored in.
11. Read the feedback. If a finding is tagged Blocking, implement it — this is your responsibility, not a decision point. If tagged Worth considering, decide yourself whether to fold it in or note it as an accepted risk. The critic reviews once; there is no re-review round after this.
12. If anything remains genuinely unresolved after asking in chat (step 5) — the user deferred, or it only became apparent while resolving the critic's feedback — write it under an "Open Questions" section at the end of plan.md.

## NOTE
- All requirements suggested by spec.md are important. Do not avoid any requirement — write a detailed plan against each one spec.md sets.
- Do not write any code or change any file. Your work is limited to writing plan.md (and its sub-task variants), invoking the review agent, and acting on its feedback.
- Mention all tests required before implementing each change. Explicitly state that tests are written first and implementation follows — this project follows TDD.
- The plan must not include changes to any existing test unless specified by spec.md and approved by the user.
- IMPORTANT: give each requirement its own section, and explicitly state how two requirements connect to each other where relevant.
- If the task is split, explicitly state this at the top of the top-level plan.md, and link to each sub-task's plan.md.

## Output
- Single-scope: specs/[issue-number]-[issue-info]/plan.md and .../plan-review.md
- Split scope: specs/[issue-number]-[issue-info]/plan.md (overview + links) and specs/[issue-number]-[issue-info]/tasks/[sub-task-number]-[sub-task-slug]/plan.md, each with its own plan-review.md in the same sub-task folder.