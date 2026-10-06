# Intent [S##] — [Step title]


> Stage: 4 :: Intent
> Intent ID: intent-[S##] (optionally intent-[S##]-[US-###])
> Build step: [S##] of the build-roadmap ([milestone, if defined])
> Serves Story: [US-### (child id if split, e.g. US-005b)] — PRD section 5a ref, or INFRA-0X for an enabler step
> Depends on intents: [intent ids for the steps this step depends on, or None]
> product: [product/Feature Name]
> product-version: [Version Number]
> Author: intent-composer-skill
> Datetime: [YYYY-MM-DD HH:MM]


## Story
As a [user], I want [capability] so that [benefit].   (from PRD; for a split story, add one line saying which part this step delivers)

## Component & data contract
[CMP-ID + the pinned interface/schema this intent implements. (from solution-architecture)]

## Libraries & build-order
[Local libraries + step number + Depends-on. (from build-roadmap)]

## Acceptance criteria
[Step-focused, binary / verifiable. These become the SDD spec's acceptance.]
- **From the story:** [criteria allocated to this step by the roadmap's split-story allocation, or the story's full PRD 5a criteria if the story was not split; keep parent criterion ids, e.g. AC-2.a]
- **Step test gate (EM-tier):** [the roadmap's test gate for this step, including manual checks]

## Out of scope
[What this intent explicitly does not cover, including what sibling steps of the same story deliver.]

## Notes for spec stage
[Anything the SDD spec author needs; e.g. expected plan fan-out.]
**Open questions (this intent only):** [list, or "None"]
