"""Tests for swarm.sync (RepositorySync)."""

import json
import os
import subprocess
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from swarm.sync import RepositorySync


# ---------------------------------------------------------------------------
# URL parsing
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("url, expected", [
    ("https://github.com/owner/repo", ("owner", "repo")),
    ("https://github.com/owner/repo.git", ("owner", "repo")),
    ("http://github.com/owner/repo", ("owner", "repo")),
    ("git@github.com:owner/repo.git", ("owner", "repo")),
    ("owner/repo", ("owner", "repo")),
])
def test_parse_repo_url(url, expected):
    assert RepositorySync._parse_repo_url(url) == expected


def test_parse_repo_url_invalid():
    with pytest.raises(ValueError):
        RepositorySync._parse_repo_url("not-a-repo")


# ---------------------------------------------------------------------------
# Constructor
# ---------------------------------------------------------------------------

def test_constructor_defaults(tmp_path):
    sync = RepositorySync("owner/repo", local_path=str(tmp_path))
    assert sync._owner == "owner"
    assert sync._repo == "repo"
    assert sync.branch == "main"
    assert sync.local_path == tmp_path


def test_constructor_custom_branch(tmp_path):
    sync = RepositorySync("owner/repo", local_path=str(tmp_path), branch="develop")
    assert sync.branch == "develop"


def test_constructor_reads_env_token(tmp_path, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "env-token")
    sync = RepositorySync("owner/repo", local_path=str(tmp_path))
    assert sync.token == "env-token"


# ---------------------------------------------------------------------------
# is_connected – mocked API
# ---------------------------------------------------------------------------

def test_is_connected_true(tmp_path):
    sync = RepositorySync("owner/repo", local_path=str(tmp_path))
    with patch.object(sync, "_api_get", return_value={"id": 1}):
        assert sync.is_connected() is True


def test_is_connected_false(tmp_path):
    from urllib.error import URLError
    sync = RepositorySync("owner/repo", local_path=str(tmp_path))
    with patch.object(sync, "_api_get", side_effect=URLError("no net")):
        assert sync.is_connected() is False


# ---------------------------------------------------------------------------
# pull / fetch – mocked subprocess
# ---------------------------------------------------------------------------

def _mock_proc(returncode=0, stdout="", stderr=""):
    proc = MagicMock()
    proc.returncode = returncode
    proc.stdout = stdout
    proc.stderr = stderr
    return proc


def test_pull_success(tmp_path):
    sync = RepositorySync("owner/repo", local_path=str(tmp_path))
    with patch("subprocess.run", return_value=_mock_proc(0)) as mock_run:
        assert sync.pull() is True
        args = mock_run.call_args[0][0]
        assert "pull" in args


def test_pull_failure(tmp_path):
    sync = RepositorySync("owner/repo", local_path=str(tmp_path))
    with patch("subprocess.run", return_value=_mock_proc(1, stderr="conflict")):
        assert sync.pull() is False


def test_fetch_success(tmp_path):
    sync = RepositorySync("owner/repo", local_path=str(tmp_path))
    with patch("subprocess.run", return_value=_mock_proc(0)) as mock_run:
        assert sync.fetch() is True
        args = mock_run.call_args[0][0]
        assert "fetch" in args


# ---------------------------------------------------------------------------
# get_latest_commit – mocked API
# ---------------------------------------------------------------------------

def test_get_latest_commit_ok(tmp_path):
    sync = RepositorySync("owner/repo", local_path=str(tmp_path))
    fake_response = {
        "sha": "abc123",
        "commit": {
            "message": "Initial commit",
            "author": {"name": "dev", "date": "2024-01-01T00:00:00Z"},
        },
    }
    with patch.object(sync, "_api_get", return_value=fake_response):
        info = sync.get_latest_commit()
    assert info["sha"] == "abc123"
    assert info["author"] == "dev"


def test_get_latest_commit_failure(tmp_path):
    from urllib.error import URLError
    sync = RepositorySync("owner/repo", local_path=str(tmp_path))
    with patch.object(sync, "_api_get", side_effect=URLError("fail")):
        assert sync.get_latest_commit() is None


# ---------------------------------------------------------------------------
# export / import snapshot
# ---------------------------------------------------------------------------

def test_export_snapshot(tmp_path):
    from swarm.coordinator import Coordinator
    sync = RepositorySync("owner/repo", local_path=str(tmp_path))
    coord = Coordinator("TestCoord")
    path = sync.export_snapshot(coord)
    assert Path(path).exists()
    data = json.loads(Path(path).read_text())
    assert data["repository"] == "owner/repo"
    assert "state" in data


def test_import_snapshot(tmp_path):
    snapshot = {"repository": "owner/repo", "branch": "main", "state": {}}
    snap_file = tmp_path / "swarm_snapshot.json"
    snap_file.write_text(json.dumps(snapshot))
    sync = RepositorySync("owner/repo", local_path=str(tmp_path))
    data = sync.import_snapshot()
    assert data["repository"] == "owner/repo"


def test_import_snapshot_missing_file(tmp_path):
    sync = RepositorySync("owner/repo", local_path=str(tmp_path))
    with pytest.raises(FileNotFoundError):
        sync.import_snapshot(str(tmp_path / "nonexistent.json"))
