# Solution Architecture — [Product]

> Stage: 2 :: Detailed Solution Architecture
> product: [product/Feature Name]
> product-version: [Version Number]
> Author: solution-architect-skill
> Datetime: [YYYY-MM-DD HH:MM]


## Topology decision
[Chosen style (e.g. modular monolith) + why. Derived from requirements, not assumed.]

## Components
For each component:

### CMP-01: [name]
- **Responsibility:** [one line]
- **Interfaces & data contracts:** [signatures / schemas crossing this boundary — the pinned contract]
- **Depends on:** [CMP-IDs or "None"]
- **Realizes:** [CAP-IDs]
- **Serves:** [US-### list]

## Cross-cutting / NFR components
[First-class components (guardrails, eval layer, security, observability). Same fields as above. Each with the NFR it enforces and, if it serves no US-###, an INFRA-## id. INFRA-## ids are defined only here.]

### CMP-0X: [name] — INFRA-01
- **Enforces:** [NFR]

## Gaps & suggested tech
[Capabilities no available tech satisfies + the tech the architect suggests.]

## Conflicts vs tech-constraints
[Where a hard constraint cannot meet a capability — surfaced for the user to decide.]

## ADR index
[Links to adr/ADR-00X — one per cross-component / expensive-to-reverse decision.]

## Diagram
[Rendered from the component list above. A view, never the source of truth.]
