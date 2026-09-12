
# Pre Execution Check

1. Read CLAUDE.md's Commands section. Two cases:
   - **Commands already exist and are real**: run each relevant one now, before implementing anything, to confirm it actually executes. If a command is missing, wrong, or stale, fix it (discover the real command from the project's own config — package.json scripts, pyproject.toml, Makefile, etc.) and update CLAUDE.md.
   - **No working test command exists yet, and plan.md itself is responsible for setting one up** (e.g. this is the first plan for this part of the stack, and installing the test framework and writing the first test is part of the plan's own scope): treat that setup as its own first step, done before any feature TDD begins. Concretely:
     a. Install the test library/framework plan.md specifies.
     b. Write and run one minimal smoke test (e.g. "1 equals 1", or a trivial existing-route check) to confirm the runner itself actually works, before writing anything feature-related.
     c. Once the runner is confirmed working, add the real command to CLAUDE.md's Commands section.
   - If neither case applies — no working command exists, and plan.md doesn't account for setting one up — stop and tell the user. Do not improvise test infrastructure plan.md never scoped.