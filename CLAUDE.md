# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project state

This is `skill-repository` — a repository for Claude agent skills, plus the code and datasets used to test those skills. `main.py` is a placeholder entry point. Skills live under `.claude/skills/<category>/<skill_name>/`; test datasets live under `datasets/<category>/<dataset_name>/`. Treat any described "architecture" as forward-looking rather than established; verify against the actual file layout before assuming structure exists.

## Dataset structure

Datasets are organized by the category of skill they're used to test: `datasets/<category>/<dataset_name>/`. Each dataset is fully self-contained and unrelated to others — no shared schema or cross-dataset joins should be assumed. Layout per dataset:

```
datasets/<category>/<dataset_name>/
├── raw/          # untouched source files, as downloaded (gitignored)
├── processed/    # cleaned/transformed intermediate data (gitignored)
├── code/         # notebooks live directly here; code/scripts/ holds common scripts for this dataset
│   └── scripts/  # importable helpers shared across this dataset's notebooks
├── output/       # final results: reports, charts, fully transformed datasets (tracked in git)
└── README.md     # what this dataset/project is, source, license, schema notes — the first thing to read for project-specific context
```

`raw/` and `processed/` are gitignored (see root `.gitignore`) since they hold large or license-restricted data files — these folders won't appear in git until they contain tracked files. `code/` and `output/` are tracked.

Current categories and datasets:
- `supply-chain/supplier-stability-dataset` — supplier stability data used to test the **procurement-analyzer** skill (`.claude/skills/supply-chain/procurement-analyzer/`). See its `README.md` for what's actually been done with it.

Do not introduce a shared `common/` utilities folder preemptively — only add one if duplicated logic actually emerges across datasets.

**Before working on any dataset, read its `README.md` first** — it documents what that specific project/analysis is about. Don't rely on this file for per-dataset specifics; it only covers repo-wide conventions.

### Notebook imports (`code/scripts/` package)

Notebooks in `code/` import their sibling `code/scripts/` package (e.g. `from scripts.component_report import ComponentReport`) with no `sys.path` hack, because `.vscode/settings.json`'s `jupyter.notebookFileRoot: "${fileDirname}"` makes each notebook's own folder the kernel's cwd. Only holds when run via VS Code's Jupyter extension — plain `jupyter lab`/`notebook` won't pick this up.

## Tooling

- Package/dependency management uses **uv** (see `uv.lock`, `pyproject.toml`). Use `uv` commands rather than raw `pip`.
- Python version is pinned via `.python-version` to `3.11` (project requires `>=3.11`).

## Common commands

```bash
# Install/sync dependencies into the uv-managed virtualenv
uv sync

# Run the main entry point
uv run main.py

# Add a new dependency
uv add <package>
```

There are no lint, test, or build tooling configured yet — no test framework, linter, or formatter is present in `pyproject.toml`.
