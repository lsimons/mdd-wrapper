# AI agent instructions for mdd-wrapper

This file (`AGENTS.md`) is the canonical agent configuration. `CLAUDE.md`
is a symlink to this file.

[README.md](README.md) explains what this is.
[CONTRIBUTING.md](CONTRIBUTING.md) explains how to contribute.

This repository is a **reference implementation**, not a product: the
smallest complete example of composing on
[`mdd`](https://github.com/schubergphilis/mdd) without forking it. It is
four source files on purpose. Before adding anything, ask whether it
demonstrates more of the composition seam; if not, it belongs in the core
or nowhere.

## Layout

```
src/mdd_wrapper/
  backend.py                 # GitHubBackend — the MirrorBackend implementation
  cli.py                     # the composition: register_backend +
                             #   register_skill_root + build_dispatcher + run
  skills/                    # bundled Claude Code skills, shipped as package-data
tests/                       # test_backend.py, test_cli.py
```

Everything else — the document model, the readers and writers, the
Confluence and SharePoint sync engines, `mdd ai` / `mdd search` /
`mdd skills` — lives in `mdd`. Look there first; the common mistake is
searching here for code that is in the dependency. `pyproject.toml`
resolves `mdd` from a sibling checkout at `../mdd`, so a change spanning
both layers is: edit `../mdd`, `mise run install`, run the gate here.

## Staying in lockstep

The value of this repo is that it does not drift. When the core changes
`MirrorBackend`, the skill roots, or `build_dispatcher`'s arguments, this
repo changes with it in the same cycle.

`tests/test_backend.py` annotates `GitHubBackend` against the
`MirrorBackend` protocol so a newly added method fails `mise run
typecheck` here. Trust that alarm; do not silence it.

## The gate

`mise run ci` — `ruff check` + `ruff format --check`, `basedpyright`
strict, the unit suite with a 90% coverage floor, then `zizmor` +
`actionlint` over the workflows. Green before review, no exceptions. Use
`uv run mdd`, because an installed `mdd` may be a different wrapper.

Tasks (`mise tasks`):

| Task | What it does |
| --- | --- |
| `install` | `uv sync --all-groups` |
| `lint` | `ruff check` + `ruff format --check` |
| `format` | `ruff format` + `ruff check --fix` |
| `typecheck` | `basedpyright` strict |
| `test` | `pytest` with coverage; floor in `pyproject.toml` |
| `audit` | `zizmor` + `actionlint` over the workflows and dependabot config |
| `ci` | the full gate: all of the above |
| `ci-watch` | watch the GitHub Actions run for the current branch |

Local `ci` passing does not mean CI passes; after pushing, use
`mise run ci-watch`.

## Agent skills

### Git remote

Use GitHub with `gh`, against `lsimons/mdd-wrapper`. A clone may have
several remotes and `origin` is not necessarily the GitHub one, so pass
`--repo lsimons/mdd-wrapper` explicitly instead of relying on the default.

### Issue tracker

Use GitHub issues on `lsimons/mdd-wrapper`. See
[`docs/agents/issue-tracker.md`](docs/agents/issue-tracker.md).

### Triage labels

Use needs-triage, needs-info, ready-for-agent, ready-for-human, wontfix.
See [`docs/agents/issue-tracker.md`](docs/agents/issue-tracker.md).

## No cross-references from code

Do not cite spec, plan, or issue numbers in `src/` or `tests/` — not in
comments, docstrings, log messages, `argparse` help, or error text. The
core's design documents are not part of this distribution and a reader
here cannot resolve them. State the rule in a sentence instead. Links to
public external standards are fine.

## This repository is public

Nothing committed here may name an internal hostname, a private
repository, an organisation's group layout, a customer, or an `op://`
vault path. Everything must be derivable from the public core alone.
Never run `op read`, `op item get`, `op signin`, or any other 1Password
command that returns secret material.

## Commits

[Conventional Commits](https://conventionalcommits.org/):
`type(scope): description`. Commit on a branch and open a PR against
`lsimons/mdd-wrapper`; PRs merge after human review.
