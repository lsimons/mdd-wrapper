# Contributing

Thanks for taking the time to look at `mdd-wrapper`.

Contributions are governed by the [Apache-2.0 licence](LICENSE), and
participation by the [Code of Conduct](CODE_OF_CONDUCT.md).

## What belongs here

This repository is a *reference*, not a product: the smallest complete
example of building on [`mdd`](https://github.com/schubergphilis/mdd)
without forking it. Two rules follow from that.

- **Keep it small.** A change that makes the wrapper bigger without
  demonstrating more of the seam does not belong. If a feature would be
  useful to everyone, it belongs in the core.
- **Track the core.** When the core changes `MirrorBackend`, the skill
  roots, or `build_dispatcher`'s arguments, this repo is expected to
  change with it. Drifting quietly is the one failure mode that makes a
  reference worse than none.

## Getting set up

```bash
mise install          # python + uv
mise run install      # uv sync --all-groups
mise run ci           # the full gate
```

`pyproject.toml` resolves `mdd` from a sibling checkout at `../mdd`, so
clone it there first. `mise install` supplies everything else the gate
needs, including `zizmor` and `actionlint`; the core's own external tools
are exercised by the core's suite, not this one.

Issues live on GitHub — see
[`docs/agents/issue-tracker.md`](docs/agents/issue-tracker.md) for the
labels and how they are used.

## The gate

`mise run ci` is the contract: `ruff check` + `ruff format --check`,
`basedpyright` in strict mode, the unit suite, then `zizmor` +
`actionlint` over the workflows. It is expected to be green before
review.

- **Coverage floor.** `mise run test` fails below 90% line coverage. The
  floor is a regression guard, not a target — do not reach it by testing
  trivia.

- **Full type annotations.** `basedpyright` runs in strict mode and must
  report zero errors. Suppress with a specific code
  (`# pyright: ignore[reportAny]`), never a bare ignore.
- **Tests for behaviour changes.** `tests/test_backend.py` pins the
  backend against the `MirrorBackend` protocol, so a method added to the
  core surfaces here as a typecheck failure rather than a runtime one.
  Keep that assertion working.
- **No live services in the unit suite.** The one job that talks to real
  Confluence and GitHub is `.github/workflows/live-sync.yml`, on a
  schedule, against sandbox accounts.

## Commits

[Conventional Commits](https://conventionalcommits.org/):
`type(scope): description`, with `type` one of `feat`, `fix`, `docs`,
`style`, `refactor`, `test`, `build`, `ci`, `perf`, `revert`,
`improvement`, `chore`.

## A note on how this is built

`mdd` and this wrapper are written largely by AI agents under human
review. That does not change what is expected of a contribution — the
gate is the gate — but it does mean the code carries unusually detailed
inline rationale. Please keep that up: explain *why*, not *what*.
[`AGENTS.md`](AGENTS.md) is the instruction file agents read.
