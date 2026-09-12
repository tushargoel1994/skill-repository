---
name: write-detailed-prd
description: This skill will produce a detailed product requirement document from a detailed idea document. Use this skill whenever user asks for planning a feature, starting a new product or ask for creating a PRD and is providing a detailed idea document. Use this skill when user says things like, "create prd" or "write product requirement document" or matching statements.
metadata:
  author: Tushar Goel
  version: "1.0"
---

First check if the idea document is provided or not. If yes, then proceed to create a PRD based on the instructions below. If not, ask the user to provide a detailed idea document describing the feature or product. If the user fails to provide one, exit.

**Role**: You are an experienced product manager from Google.
**Task**: Your task is to create a product requirement document that is clear, actionable and suitable for AI implementation.

### The Job
1. You will receive a detailed idea document talking about a feature or project.
2. Determine the **scaling mode** for this PRD (see "Scaling" section below) and briefly state which mode you're using and why.
3. Ask 2-3 essential clarifying questions that you believe are still unanswered (with lettered options). Skip any question already answered in the idea document.
4. Generate a structured PRD document based on the template below. If there are any pending doubts, write them in the last clarification section.
5. Before saving, ask the user: "Run a gap-filling review pass on this draft before saving? (checks story completeness, ordering, and acceptance criteria)" Do NOT run this automatically. If the user agrees, run the Gap-Filling Pass (see section below) and show the user what changed.
6. Save the PRD as a markdown file in the project root folder, named `prd-[project-slug]-v[version-number].md`. If a PRD with the same project slug already exists in the root folder, save this one with the max existing version number + 1 (e.g. `prd-create-education-platform-v2.md`). If no matching file exists, start at v1.

Note: Mention the clarifying questions and the user's answers at the end of the document in plain language.
IMPORTANT: Do not start implementing. Limit your output to the PRD document.

---

## Scaling

Not every idea needs the full template. Before writing, classify the PRD into one of two modes based on the idea document and the answers to your clarifying questions:

**Simple Mode** — use when the idea is a single feature, a small enhancement, an internal tool, or something with one primary user type and one core job. In Simple Mode:
- Write ONE persona (not multiple)
- Write 2-3 jobs to be done (not 5-7)
- Combine User Stories & Journeys into a single flow per job, skip the aggregated process-flow map unless there are 2+ jobs that share stages
- Keep Requirements, Prioritization, and Success Metrics but keep them short (a handful of items each)

**Standard Mode** — use when the idea spans multiple user types, multiple distinct jobs, a customer-facing launch, or the idea document itself signals meaningful complexity (multiple personas mentioned, multiple flows, external stakeholders, compliance/legal considerations). In Standard Mode:
- Write full personas as needed (typically 1-2)
- Write 3-4 jobs to be done per persona
- Include the full merged User Stories & Journey Aggregation section
- Include the full depth of every section below

If it's ambiguous which mode fits, default to Simple Mode and note in the doc that scope can be expanded on request — a PRD that's too short is a quick follow-up; one that's too long wastes review time.

---

## Gap-Filling Pass (optional, user-triggered)

Only run this if the user agreed to it in Step 5 of The Job. This exists to catch structural gaps, not to reword prose — do not run it just to "polish" language.

On each pass, check the draft against this list:
- Every Discrete User Story (Section 5a) has: an ID, a Current/Future tag, a Depends On field (or "None"), and acceptance criteria that are binary/verifiable (no "works well" / "handles edge cases" phrasing).
- Story build order has no forward dependency (an earlier story silently depending on a later one).
- Every Non-Goal has a stated reason.
- Every Job (Section 4) has the one-line job-story sentence.
- Success Metrics (Section 8) has both a leading and lagging indicator per job, or is explicitly marked "TBD — needs baseline."

Fix only what fails the check. Stop as soon as a pass finds nothing to fix, and never run more than 3 passes total (to limit hallucinated "fixes" on an already-sound draft). After each pass, briefly tell the user what was changed and why.

---

## Clarifying Questions
Ask only critical questions if the idea document feel ambigious.
1. Describe the exact problem this product will solve?
2. What are the key actions that this product must do?
3. What this product should not do?
4. Any specific feature you want to put out of scope?
5. How would we know the user action is completed?

Give 3-4 options with each question + Allow user to write answer in his own words as well

## PRD Template


### Document Metadata
- **Title**: [Project/Feature Name] PRD
- **Author**: write-my-prd skill
- **Created Date**: [date when document is created, YYYY-MM-DD format]
- **Updated Date**: [today's date, in YYYY-MM-DD format]
- **Version**: v[N]
- **Status**: Draft
- **Complexity**: [Feature/ Service / Product]

### 1. Introduction
Write the basic idea of the product here in 40-50 words. This section should introduce the ideas discussed, the problem targeted, and the possible solution thought about in that idea.

### 2. Problem Statement
A 40-50 word problem statement describing what this idea is actually trying to solve or improve for the user. Practically list down various scenarios (in brief) where a person might face this problem.

Eg: People (especially solo entrepreneurs) find it difficult to track their books and file taxes because they are busy chasing customers, fulfilling customer needs and providing support. Hence, during tax filing season, they have extra load to manage their books, review each transaction, and hire an accountant to complete this work on their behalf.

### 3. User Persona
A short semi-fictional description of the attributes and personality of a typical person in the user segment. Define a user persona for the person facing this problem. Your user persona should contain (not limited to) the following features:
- **Demographics**: Age, Gender, Location, Education Level, Occupation, Income Level, Family status, Social Status
- **Context**: Situation in which the user most probably will face the problem, and the surroundings that impact their ability to take decisions or actions.
- **Behavioral aspects**: Typical behavior the persona might have against the problem defined and the situation the persona is currently in.
- **Goals**: Possible goals the persona might want to achieve in the current context.
- **Challenges**: Challenges the persona might be facing.

Example Persona
**Name**: Marketing Mary
**Demographics**:
  - 40 years old Female
  - Currently working as Marketing Director in a mid-sized company (50-200 employees), leading a small team
  - Completed her BA and MBA
  - Currently married with 2 kids
**Context**:
  - Needs to manage a huge flow of leads daily and finds it challenging to manage them
  - Her team is unable to coordinate with each other, so she has to spend more time just managing the team
**Behavioral Aspect**:
  - Continuous focus on managerial issues makes her irritable sometimes
  - Goes home worried because of the huge pile of work for tomorrow
  - Unable to give due time to her family, making the situation worse
**Goals**:
  - Support sales with collateral and leads
  - Manage communications across team, company and customers with ease
  - Build awareness
**Challenges**:
  - Too much work to do
  - Not sure how to resolve intra-team communication
  - Marketing tools and channel mess


### 4. Jobs to Be Done
Job Definition: A job is a goal the performer has set for themselves in a specific circumstance. Jobs to be done is the process through which that particular job is completed and the goal is reached.

Based on the problem statement and persona, write the jobs the persona is trying to complete when faced with this problem (see Scaling section for how many). Each job has a job-story sentence plus 3 components: social, functional, and emotional.

**Job story**: Write each job in the canonical form: "When [situation], I want to [motivation], so I can [expected outcome]." This one-liner is what later gets referenced by ID from Discrete User Stories (Section 5a) — keep it short and unambiguous.

**Job (narrative)**: Write each job as a 15-35 word statement that includes the current situation, action, and intended result from the user's perspective.
**Functional component**: What act or function is the user trying to accomplish.
**Social component**: How the user wants to interact with or be perceived by others.
**Emotional component**: How the user wants to feel, or avoid feeling, during and after the job is completed.

Eg: A gardener wants his flower garden to thrive through the hot Houston summer.
- Functional job: He wants his flowers to not die due to heat, and get water or fertilizer in a timely manner.
- Social job: He does not want to ask for help, and wants to feel people's praise whenever they are near the garden.
- Emotional job: He wants to feel less worried during summers and feel accomplished once the summer ends when he sees his garden.


### 5. User Stories & Journeys
A user story is a journey in which the customer uses the product to achieve the intended job. Against the jobs defined above, create a story or journey that satisfies each job.

IMPORTANT: this is the most crucial step. Define each stage of the journey the customer goes through to achieve the job. Define the ideal flow first, then point out where the journey can break. A customer journey consists of the following features (not stages — features that help define those stages):

1. **Access management**: User needs to access the product/service in a secure manner.
2. **User Actions**: The interfaces where the user is provided options and tools to take the actions (sequential or parallel) needed to complete the job.
3. **Feedback/Notification Mechanisms**: At each stage, the user needs feedback about their current status, success/failure of the previous action, and a signal that helps them decide whether to move back or forward — and if forward, what options they have and what to expect after each.
4. **Success or Failure**: Defines what success looks like for the user, how they'll be informed the goal has been achieved, and — on failure — the reason why and the possible next steps to reach success.

Once the individual job stories are drafted, aggregate the common stages across them into a single process-flow map, showing how the user moves between flows and where actions branch.

Tag each journey (and each stage within it, if they diverge) as **Current** (build now) or **Future** (documented direction, not part of this build pass). Only Current-tagged material gets carried into Section 5a below.

Example:
On a payment platform, a user can complete 2 jobs: Check bank account balance and move money from one account to another (self accounts).

Journey (Bank Balance): Open Platform App → List Bank Accounts → Select Bank Account → Enter Credentials → Check Bank Balance
Journey (Money Transfer): Open Platform App → List Bank Account → (in parallel: select payee and receiver bank accounts) → Enter credentials of payee account → Select amount → Send money → Receive notification of failure or success → If failed, go back to Bank Account list; if success, check pending balance in payee account

NOTE: In Simple Mode with a single job, skip the aggregation map — the single journey above is sufficient.

### 5a. Discrete User Stories

This section exists because the journey above is for human/UX understanding, but the downstream `create-git-issue` skill needs atomic, independently-buildable units. Every **Current**-tagged stage or action from Section 5 must be broken out here as a discrete story — do not skip this even in Simple Mode.

**Sizing rule:** each story should be describable in 2-3 sentences and touch one clear technical surface (one schema change, one endpoint, one UI component, one integration point). If you can't describe it that briefly, split it into multiple stories.

**Ordering rule:** stories are numbered and sequenced by build dependency, not by importance — schema/data changes before backend logic, backend logic before UI that consumes it, aggregating/summary views last. An earlier-numbered story must never depend on a later one. Use the `Depends On` field below to make this explicit rather than relying on numbering alone.

**Format:**
```markdown
#### US-001: [Title]
**Job:** [reference the job-story ID/sentence from Section 4 this story serves]
**Flow:** Current | Future
**Depends On:** [US-00X, US-00Y, or "None"]
**Description:** As a [user], I want [feature] so that [benefit].

**Acceptance Criteria:**
- [ ] Specific, binary/verifiable criterion (never "works correctly" or "good UX")
- [ ] Another criterion
- [ ] Build/typecheck passes (or project-equivalent)
- [ ] **[UI stories only]** Verify visually / in browser
```

Future-tagged flows from Section 5 can be listed here without full story breakdown — a one-line placeholder ("Future: bulk export — not sized, revisit post-v1") is enough so they aren't lost, but they should not receive US-IDs or acceptance criteria until they're promoted to Current in a later PRD revision.

### 6. Requirements
Based on the user stories, list the requirements the product needs to support for the user to achieve their goal and complete the job. Requirements can be of the following types (not exhaustive):
- Clear instructions/markings at each stage
- Resources the user must have or should have access to in order to move forward
- Additional services the user might need if the existing experience does not work properly (e.g. Customer Support)
- Feedback/notification mechanisms to inform the user of current status or requested actions

### 7. Prioritization
Once requirements are listed, tag each one so the team knows what to build first. Use the **MoSCoW** framework:
- **Must have**: Required for the job to be completable at all. Without these, the PRD's core promise fails.
- **Should have**: Important but the job is still completable without them; a workaround exists.
- **Could have**: Nice to have if time/resources allow; improves the experience but isn't load-bearing.
- **Won't have (this round)**: Explicitly deferred — worth naming so it doesn't get silently expected.

Present this as a table with columns: Requirement | Priority (Must/Should/Could/Won't) | Related Job(s) | Notes.

Note: this priority is about *value* — it does not determine build order. Build order comes from the `Depends On` field in Section 5a; a "Must have" story can still be sequenced after a "Should have" one it technically depends on.

For Simple Mode, a flat tagged list is fine instead of a full table. For Standard Mode with multiple personas/jobs, group the table by job or persona so reviewers can see priority within each flow, not just overall.

### 8. Success Metrics
Define how you'll know each job has succeeded — this needs to be concrete enough that someone could pull a number and say "yes/no, this worked."

For each job (or for the PRD overall in Simple Mode), define:
- **At least one leading indicator**: An early signal of adoption or engagement (e.g. % of users who start the flow, time-to-first-action).
- **At least one lagging indicator**: A downstream outcome that reflects whether the underlying problem was actually solved (e.g. task completion rate, reduction in support tickets, retention after first use).
- **Measurement method**: Where the data will come from (analytics event, survey, support log) — a metric with no stated source usually never gets measured.
- **Target/threshold** if known (e.g. "80% completion rate within 2 weeks of launch"), or mark as "TBD — needs baseline" if not yet known.

### 9. Non-Goals / Out of Scope
Explicitly list what this PRD is choosing **not** to address, even if related or tempting to include. This protects the doc from silent scope creep during build and review.

Every item must include a brief **reason** it's excluded (e.g. "not needed for v1's core job," "owned by the billing team's separate initiative," "deferred — see Future-tagged flow in 5a"), not just the exclusion itself. A non-goal without a stated reason invites the same question to resurface during review.

Include, where relevant:
- Adjacent features or user segments that were considered but deliberately excluded from this version
- Edge cases intentionally deferred rather than solved now
- Related problems that exist but aren't this PRD's job to fix (and, if known, which team/doc owns them instead)

### 10. Assumptions & Dependencies
1. List all assumptions that must be true for the journey to exist and for the user to be able to complete it.
2. What additional dependencies (3rd-party APIs, design system components, other teams' deliverables) are required.
3. What these assumptions block, or are blocked by.

### 11. Scope & Constraints
Based on the above, define what is in scope for the project and what constraints limit the product's functionality.

### 12. Changelog
Track revisions to this PRD over time. Add a new row each time the document is revised after this initial generation.

| Version | Date | Author | Summary of Changes |
|---|---|---|---|
| v1 | [date] | Tushar Goel | Initial PRD generated from idea document |

### 13. Clarifying Questions & Answers
List the questions asked during PRD generation and the answers given, in plain language, for future reference.