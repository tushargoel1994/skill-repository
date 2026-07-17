# skill-repository

This repository contains various Claude agent skills, along with the code and datasets used to test those skills.

## Structure

Test datasets live under `datasets/<category>/<dataset_name>/`, grouped by the category of skill being tested. Each dataset is fully self-contained (own `raw/`, `processed/`, `code/` with notebooks + a `scripts/` package, `output/`, `README.md`) — see `CLAUDE.md` for the exact per-dataset layout and conventions.

Notebooks in `code/` import their sibling `code/scripts/` package with no `sys.path`/`PYTHONPATH` hack — see CLAUDE.md's "Notebook imports" section for the mechanism.

**Read each dataset's own `README.md` before working on it** — it explains what that specific dataset/project is about (source, what's been analyzed, current state); this file only covers repo-wide structure.

## Current datasets

| Category | Dataset | Skill tested | Why it's here |
|---|---|---|---|
| supply-chain | [`supplier-stability-dataset`](./datasets/supply-chain/supplier-stability-dataset/README.md) | procurement-analyzer | 517-order supplier/procurement dataset (44 suppliers, 6 component categories, 3 criticality tiers) used to exercise the skill against five realistic procurement scenarios — supplier rationalization, single-source risk, renewal negotiation, project schedule root-cause, and cost-creep audits. |

## Tooling

Dependency management uses [uv](https://github.com/astral-sh/uv). See `CLAUDE.md` for common commands and repo conventions used by Claude Code when working in this repository.
