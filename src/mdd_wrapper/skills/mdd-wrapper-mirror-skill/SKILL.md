---
name: mdd-wrapper-mirror-skill
description: |
  How this wrapper decides where a synced mirror is pushed, and what to check
  when a push is refused. Use when `mdd confluence sync-space --push` or
  `mdd sharepoint sync-site --push` fails on the mirror step.
---

## When to use

Trigger this skill when the user is running `mdd` from `mdd-wrapper` and:

- a `--push` run failed with "refusing to push";
- they ask where a mirror will be pushed, or why it went to the wrong place;
- they want to point mirrors at a different GitHub owner.

## What the wrapper decides

Everything about the sync is the core's; only the push destination is this
wrapper's. `GitHubBackend` resolves a mirror to
`https://github.com/<owner>/<repo>.git`, where:

- `<owner>` is `MDD_WRAPPER_GITHUB_OWNER`, defaulting to the value baked into
  `mdd_wrapper.cli.DEFAULT_OWNER`;
- `<repo>` is the `MirrorTarget.key` — the Confluence space key or the
  SharePoint site name — unless a per-kind override was passed to the
  backend's `repo_for`.

The repository is never created for you. The backend holds no GitHub
credential, so a missing repository surfaces as a plain `git push` failure.

## Diagnosing "refusing to push"

`guard_remote` rejects a work-tree whose `origin` is not under the configured
owner on `github.com`, lookalike hosts included. In order:

1. `git -C <mirror> remote get-url origin` — read the actual remote.
2. Compare its host and owner against `MDD_WRAPPER_GITHUB_OWNER`.
3. A stale clone, a copied `.git`, or a typo in the owner are the usual
   causes. Fix the remote or the environment variable; do not disable
   the guard.

An origin the parser does not recognise — anything that is not
`git@host:owner/repo` or `https://host/owner/repo` — is also refused, on
purpose: an unparseable remote cannot be shown to be ours.

## Where a link back to the mirror comes from

The Confluence page footer links to the mirrored file through the backend's
`web_url`, which builds GitHub's `/blob/<branch>/<path>` shape from the
work-tree's `origin`. It returns nothing — and the footer omits the link
rather than failing — when the file is not in a git work-tree, there is no
`origin`, or `origin` is not on `github.com`.
