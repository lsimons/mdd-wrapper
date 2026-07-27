# mdd-wrapper

A reference wrapper for [`mdd`](https://github.com/schubergphilis/mdd),
demonstrating its extension seam by mirroring synced documents to GitHub
instead of wherever the core would otherwise push them.

It exists for two reasons: to be the smallest complete example of
building on `mdd` without forking it, and to be the public end-to-end
test that the Confluence sync engine and the mirror seam actually work
against real services.

## What a wrapper is

`mdd` keeps documents in sync between Markdown-in-git and Confluence /
SharePoint. Everything about that is generic except *where the mirror
gets pushed* — which forge, which URL, whether the remote gets
auto-created, and what must never be pushed at all.

That is the `MirrorBackend` seam: four small operations, plus a `push`
most backends inherit. A wrapper implements them and composes a CLI:

```python
# src/mdd_wrapper/cli.py — the whole thing
from mdd.cli import build_dispatcher
from mdd.mirror import register_backend

from mdd_wrapper.backend import GitHubBackend


def main(argv=None):
    register_backend("github", GitHubBackend("lsimons"))
    parser = build_dispatcher(default_backend="github")
    ns = parser.parse_args(argv)
    return ns.func(ns)
```

`build_dispatcher` takes exactly two extension points — the default
backend name, and a list of command modules to append. This wrapper uses
only the first, so it ships the core command set unchanged with a
different push destination. A wrapper that also adds subcommands passes
`extra_commands=(...)`.

See [`src/mdd_wrapper/backend.py`](src/mdd_wrapper/backend.py) for the
backend itself. The interesting part is how little it has to do: remote
resolution and a host guard. Commit, rebase, push and the cold-start
bootstrap are all inherited from `GenericGitBackend`.

## Install

```bash
uv tool install git+https://github.com/lsimons/mdd-wrapper
mdd --version
```

This wrapper claims the `mdd` console-script name. That is safe here
because it is the only distribution being installed as a tool — an
isolated tool install exposes scripts from the named package only. Two
distributions both declaring `mdd` do **not** resolve in the installed
one's favour under `uv`; if you are building a wrapper that has to
coexist with another claimant, have your installer own `bin/mdd`
explicitly instead.

## Configure

```bash
export MDD_WRAPPER_GITHUB_OWNER=your-github-user   # defaults to `lsimons`
```

Mirrors resolve to `github.com/<owner>/<space-or-site-name>`. Confluence
and SharePoint credentials come from `~/.config/mdd/` exactly as they do
for the core; see the upstream README.

## Safety

`GitHubBackend.guard_remote` refuses to push a work-tree whose `origin`
is not under the configured owner on `github.com`, lookalike hosts
included. A mirror directory is easy to point at the wrong remote by
accident — a stale clone, a copied `.git`, a typo — and pushing document
mirrors somewhere unintended is precisely what the seam is meant to make
hard.

## Development

```bash
mise run install
mise run ci        # lint + typecheck + tests
```

`pyproject.toml` pins `mdd` by git tag. For local work against a sibling
checkout, switch `[tool.uv.sources]` to
`mdd = { path = "../mdd-open", editable = true }`.

## Licence

[Apache-2.0](LICENSE).
