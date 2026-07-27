"""A GitHub mirror backend — the worked example of the `MirrorBackend` seam.

`mdd`'s sync engines end a run by committing the mirror work-tree and
(optionally) pushing it somewhere. *Where* is the only provider-specific
part, and it is expressed as four operations:

- :meth:`resolve_remote` — the clone URL for a target, used to bootstrap a
  mirror that is not a git repository yet;
- :meth:`ensure_remote` — create the remote project if it is missing;
- :meth:`guard_remote` — refuse pushes that must not happen;
- :meth:`reachable` — a cheap connectivity probe;

plus :meth:`push`, which most backends leave as plain git.

This one resolves every target to a repository under a single GitHub
owner. It is deliberately small: the interesting content is what it
*doesn't* have to reimplement.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from urllib.parse import urlsplit

from mdd.mirror import EnsureOutcome, GenericGitBackend
from mdd.mirror.errors import MirrorPushError

if TYPE_CHECKING:
    from pathlib import Path

    from mdd.mirror import MirrorTarget

GITHUB_HOST = "github.com"


class GitHubBackend(GenericGitBackend):
    """Mirror to ``github.com/<owner>/<repo>``.

    Subclasses :class:`~mdd.mirror.git.GenericGitBackend` because the push
    itself is ordinary git; only remote resolution and the host guard
    differ. Remote *creation* is out of scope — this backend assumes the
    repository exists, which keeps it free of any GitHub API credential.
    """

    def __init__(self, owner: str, *, repo_for: dict[str, str] | None = None) -> None:
        """Set up a backend mirroring into ``github.com/<owner>/``.

        Args:
            owner: GitHub user or organisation that owns the mirrors.
            repo_for: Optional per-``MirrorTarget.kind`` repository name.
                A kind with no entry falls back to the target's key, which
                is what most deployments want (one repo per space/site).
        """
        self.owner = owner
        self._repo_for = repo_for or {}

    def _repo(self, target: MirrorTarget) -> str:
        return self._repo_for.get(target.kind, target.key)

    def resolve_remote(self, target: MirrorTarget) -> str:
        return f"https://{GITHUB_HOST}/{self.owner}/{self._repo(target)}.git"

    def ensure_remote(self, target: MirrorTarget) -> EnsureOutcome:
        # No auto-create: this backend holds no GitHub credential, so a
        # missing repository surfaces as a push failure with git's own
        # message rather than as a second, less informative error here.
        return EnsureOutcome(status="exists", remote_url=self.resolve_remote(target))

    def guard_remote(self, path: Path) -> None:
        """Refuse to push a work-tree whose ``origin`` is not our GitHub owner.

        The guard exists because a mirror directory is easy to point at the
        wrong remote by accident — a stale clone, a copied `.git`, a typo in
        a config. Pushing document mirrors to an unintended host is exactly
        the failure this seam is meant to make hard.
        """
        from mdd.utils.git import GitError, run_git  # noqa: PLC0415  # avoid an import cycle

        try:
            origin = run_git(["remote", "get-url", "origin"], path, timeout=10).stdout.strip()
        except GitError as exc:
            raise MirrorPushError(f"{path}: no 'origin' remote to guard: {exc}") from exc

        host, owner = _split_owner(origin)
        if host != GITHUB_HOST or owner != self.owner.lower():
            raise MirrorPushError(
                f"refusing to push {path}: origin is {origin!r}, "
                f"but this backend only writes to {GITHUB_HOST}/{self.owner}/"
            )

    def reachable(self) -> bool:
        # github.com needs no VPN; let the push report a real network
        # failure rather than pre-empting it with a guess.
        return True


def _split_owner(url: str) -> tuple[str, str]:
    """Return ``(lowercased host, lowercased first path segment)`` from a clone URL.

    Handles both ``git@github.com:owner/repo.git`` and
    ``https://github.com/owner/repo.git``. Returns empty strings for
    anything unrecognised, which the caller treats as "not ours".
    """
    if url.startswith("git@"):
        host, _, path = url[len("git@") :].partition(":")
    elif url.startswith(("https://", "http://")):
        parts = urlsplit(url)
        host, path = parts.hostname or "", parts.path
    else:
        return "", ""
    segments = [s for s in path.strip("/").split("/") if s]
    return host.lower(), segments[0].lower() if segments else ""
