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

That is the `MirrorBackend` seam: five small operations, plus a `push`
most backends inherit. A wrapper implements them and composes a CLI:

```python
# src/mdd_wrapper/cli.py — the whole thing
from importlib.resources import files
from pathlib import Path

from mdd.cli import build_dispatcher, run
from mdd.commands import register_skill_root
from mdd.mirror import register_backend

from mdd_wrapper.backend import GitHubBackend


def main(argv=None):
    register_backend("github", GitHubBackend("lsimons"))
    register_skill_root(Path(str(files("mdd_wrapper") / "skills")))
    parser = build_dispatcher(
        default_backend="github",
        version="mdd-wrapper 0.1.0",
    )
    return run(parser, argv)
```

That is the whole composition surface:

| Call | What it lets a wrapper change |
| --- | --- |
| `register_backend` | where a synced mirror is pushed |
| `register_skill_root` | which Claude Code skills `mdd skills` ships |
| `build_dispatcher(default_backend=…)` | which backend is the default |
| `build_dispatcher(extra_commands=…)` | extra `mdd` subcommands |
| `build_dispatcher(version=…)` | what `mdd --version` prints |
| `run(parser, argv)` | nothing — but skipping it breaks `-v` / `--trace` |

This wrapper adds no subcommands, so it ships the core command set
unchanged with a different push destination and one extra skill.

`run` is worth a word: it parses, applies the root logging flags, and
dispatches. A wrapper that calls `parse_args` itself accepts `-v`,
`--trace`, `--trace-bodies` and `--log-level` and then silently ignores
them, because the core applies them inside `run`.

See [`src/mdd_wrapper/backend.py`](src/mdd_wrapper/backend.py) for the
backend itself. The interesting part is how little it has to do: remote
resolution, a host guard, and GitHub's blob-URL shape. Commit, rebase,
push, clone-URL parsing and the cold-start bootstrap are all inherited or
imported from the core.

## Install

```bash
uv tool install git+https://github.com/lsimons/mdd-wrapper
mdd --version          # mdd-wrapper 0.1.0 (mdd 0.1.1)
```

`--version` names both: this distribution is the one you installed and
the one a bug report is filed against, while the core supplies every
command you actually run.

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

## Skills

`mdd skills list` shows the core's bundled Claude Code skills plus this
wrapper's one, tagged with the root each came from:

```
Skill roots (last registered wins on a name collision):
  [1] .../site-packages/mdd/skills
  [2] .../site-packages/mdd_wrapper/skills

  mdd-confluence-skill              available     [1]
  mdd-wrapper-mirror-skill          available     [2]
```

The bundle is data, not a package, so `pyproject.toml` ships it via
`[tool.setuptools.package-data]`. Forget that and the wheel builds fine
while `mdd skills list` finds nothing — the likeliest way to ship a
broken skill root.

## Development

```bash
mise run install
mise run ci        # lint + typecheck + tests
```

`pyproject.toml` expects mdd checked out alongside this repo, at `../mdd`
— CI clones it there too. The committed `uv.lock` pins the third-party
closure against that checkout; refresh it with `uv lock` after changing a
dependency.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). `mise run ci` is the gate.

## Security

Please report vulnerabilities privately, not as a GitHub issue. See
[`SECURITY.md`](SECURITY.md) for the reporting channels, what is in
scope, and what to expect.

## Licence

Copyright 2026 Schuberg Philis B.V.

Licensed under the Apache License, Version 2.0 (the "License"); you may
not use these files except in compliance with the License. You may obtain
a copy of the License in [`LICENSE`](LICENSE) or at
<https://www.apache.org/licenses/LICENSE-2.0>.

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
License for the specific language governing permissions and limitations
under the License.
