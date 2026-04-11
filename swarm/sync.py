"""
swarm/sync.py – Repository synchronisation for the MyClaw Swarm System.

RepositorySync connects a running swarm to its GitHub repository so that:
  • Configuration changes pushed to the repo are pulled into the swarm.
  • Agent status and metrics can be written back to the repo (optional).
  • The swarm state can be exported/imported as a JSON snapshot.

The module is deliberately dependency-light: it uses only the Python
standard library plus optional ``requests`` (for GitHub API calls) and
``gitpython`` / ``pygit2`` are intentionally avoided to keep the footprint
minimal.  The GitHub REST v3 API is used for remote operations.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

_GITHUB_API_BASE = "https://api.github.com"


class RepositorySync:
    """Connects and synchronises the swarm with a GitHub repository.

    Parameters:
        repo_url: HTTPS clone URL or ``owner/repo`` shorthand.
        local_path: Path to the local clone of the repository.
        token: GitHub personal access token (or ``None`` for public repos).
        branch: Branch to track (default: ``main``).
    """

    def __init__(
        self,
        repo_url: str,
        local_path: Optional[str] = None,
        token: Optional[str] = None,
        branch: str = "main",
    ) -> None:
        self.repo_url: str = repo_url
        self.local_path: Path = Path(local_path) if local_path else Path.cwd()
        self.token: Optional[str] = token or os.environ.get("GITHUB_TOKEN")
        self.branch: str = branch
        self._owner, self._repo = self._parse_repo_url(repo_url)
        logger.info(
            "RepositorySync initialised for %s/%s (branch=%s, local=%s).",
            self._owner,
            self._repo,
            self.branch,
            self.local_path,
        )

    # ------------------------------------------------------------------
    # URL / identifier helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_repo_url(url: str) -> tuple[str, str]:
        """Extract ``(owner, repo)`` from a GitHub URL or ``owner/repo`` string."""
        url = url.rstrip("/")
        # Strip .git suffix
        if url.endswith(".git"):
            url = url[:-4]
        # https://github.com/owner/repo  or  git@github.com:owner/repo
        for prefix in (
            "https://github.com/",
            "http://github.com/",
            "git@github.com:",
        ):
            if url.startswith(prefix):
                url = url[len(prefix):]
                break
        parts = url.split("/")
        if len(parts) < 2:
            raise ValueError(
                f"Cannot parse owner/repo from '{url}'. "
                "Provide a full GitHub URL or 'owner/repo' shorthand."
            )
        return parts[-2], parts[-1]

    # ------------------------------------------------------------------
    # Local git helpers (subprocess-based, no extra deps)
    # ------------------------------------------------------------------

    def _run_git(self, *args: str) -> subprocess.CompletedProcess:
        """Run a git command inside *self.local_path* and return the result."""
        cmd = ["git", "-C", str(self.local_path), *args]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            logger.warning("git %s failed: %s", " ".join(args), result.stderr.strip())
        return result

    # ------------------------------------------------------------------
    # Connection check
    # ------------------------------------------------------------------

    def is_connected(self) -> bool:
        """Return ``True`` if the GitHub API is reachable and the repo exists."""
        try:
            self._api_get(f"repos/{self._owner}/{self._repo}")
            return True
        except (HTTPError, URLError, ValueError):
            return False

    # ------------------------------------------------------------------
    # Sync operations
    # ------------------------------------------------------------------

    def pull(self) -> bool:
        """Pull latest changes from the remote branch into the local clone.

        Returns:
            ``True`` on success, ``False`` otherwise.
        """
        result = self._run_git("pull", "origin", self.branch)
        success = result.returncode == 0
        if success:
            logger.info(
                "Pulled latest changes from %s/%s:%s.",
                self._owner,
                self._repo,
                self.branch,
            )
        return success

    def fetch(self) -> bool:
        """Fetch remote refs without merging.

        Returns:
            ``True`` on success, ``False`` otherwise.
        """
        result = self._run_git("fetch", "origin", self.branch)
        success = result.returncode == 0
        if success:
            logger.info(
                "Fetched refs from %s/%s:%s.",
                self._owner,
                self._repo,
                self.branch,
            )
        return success

    def get_latest_commit(self) -> Optional[Dict[str, Any]]:
        """Return metadata for the latest commit on the tracked branch.

        Uses the GitHub Commits API so no local clone is required.

        Returns:
            Dict with ``sha``, ``message``, ``author``, and ``timestamp`` keys,
            or ``None`` on failure.
        """
        try:
            data = self._api_get(
                f"repos/{self._owner}/{self._repo}/commits/{self.branch}"
            )
            commit = data.get("commit", {})
            return {
                "sha": data.get("sha", ""),
                "message": commit.get("message", ""),
                "author": commit.get("author", {}).get("name", ""),
                "timestamp": commit.get("author", {}).get("date", ""),
            }
        except (HTTPError, URLError, ValueError, KeyError) as exc:
            logger.error("Failed to fetch latest commit: %s", exc)
            return None

    # ------------------------------------------------------------------
    # Snapshot export / import
    # ------------------------------------------------------------------

    def export_snapshot(self, coordinator: Any, output_path: Optional[str] = None) -> str:
        """Export the current swarm state as a JSON snapshot file.

        Args:
            coordinator: A :class:`~swarm.coordinator.Coordinator` instance.
            output_path: File path to write.  Defaults to
                ``<local_path>/swarm_snapshot.json``.

        Returns:
            Path of the written file.
        """
        snapshot = {
            "exported_at": datetime.now(tz=timezone.utc).isoformat(),
            "repository": f"{self._owner}/{self._repo}",
            "branch": self.branch,
            "state": coordinator.status(),
        }
        path = Path(output_path) if output_path else self.local_path / "swarm_snapshot.json"
        path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
        logger.info("Swarm snapshot exported to '%s'.", path)
        return str(path)

    def import_snapshot(self, snapshot_path: Optional[str] = None) -> dict:
        """Import a previously exported swarm snapshot.

        Args:
            snapshot_path: Path to the JSON file.  Defaults to
                ``<local_path>/swarm_snapshot.json``.

        Returns:
            The parsed snapshot dictionary.
        """
        path = Path(snapshot_path) if snapshot_path else self.local_path / "swarm_snapshot.json"
        if not path.exists():
            raise FileNotFoundError(f"Snapshot file not found: {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        logger.info("Swarm snapshot imported from '%s'.", path)
        return data

    # ------------------------------------------------------------------
    # GitHub REST API helper
    # ------------------------------------------------------------------

    def _api_get(self, endpoint: str) -> dict:
        """Perform a GET request against the GitHub REST v3 API.

        Args:
            endpoint: Path relative to ``https://api.github.com/``.

        Returns:
            Parsed JSON response body.

        Raises:
            urllib.error.HTTPError: On non-2xx responses.
            urllib.error.URLError: On network errors.
            ValueError: If the response body is not valid JSON.
        """
        url = f"{_GITHUB_API_BASE}/{endpoint}"
        headers: Dict[str, str] = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        req = Request(url, headers=headers)  # noqa: S310  (no user-controlled URL)
        with urlopen(req, timeout=15) as resp:  # noqa: S310
            return json.loads(resp.read().decode("utf-8"))

    # ------------------------------------------------------------------
    # Representation
    # ------------------------------------------------------------------

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"RepositorySync(repo={self._owner}/{self._repo!r}, "
            f"branch={self.branch!r}, local={self.local_path!r})"
        )
