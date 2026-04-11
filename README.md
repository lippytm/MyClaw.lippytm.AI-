# MyClaw.lippytm.AI

Building cross-platform and cross-channel communications and integration for
**AI Swarm Communications Management and Networking Systems**.

---

## Overview

The `swarm` package provides the core infrastructure for connecting, syncing,
and coordinating networks of AI agents across multiple channels and platforms.

| Module | Purpose |
|---|---|
| `swarm/agent.py` | Autonomous AI Agent – sends/receives messages, registers handlers |
| `swarm/messaging.py` | `Message` data class + `MessageBus` pub/sub broker |
| `swarm/network.py` | Logical Network grouping agents on a shared `MessageBus` |
| `swarm/coordinator.py` | Swarm Coordinator – manages networks, routes tasks |
| `swarm/sync.py` | `RepositorySync` – connects & syncs the swarm with its GitHub repo |

---

## Quick Start

```python
from swarm import Agent, Coordinator, RepositorySync

# 1. Create a coordinator and a network
coord = Coordinator(name="MainCoord")
network = coord.create_network("primary")

# 2. Create agents and assign them to the network
agent = Agent("Worker-1", capabilities=["nlp"])
coord.assign_agent(agent, "primary")

# 3. Connect and sync with the GitHub repository
sync = RepositorySync(
    repo_url="lippytm/MyClaw.lippytm.AI-",
    local_path=".",          # path to local clone
    branch="main",
)

print("Connected:", sync.is_connected())
sync.pull()                        # pull latest changes from remote
latest = sync.get_latest_commit()  # fetch metadata of the latest commit
print("Latest commit:", latest)

# 4. Export a swarm snapshot (JSON) and import it back
snapshot_path = sync.export_snapshot(coord)
state = sync.import_snapshot(snapshot_path)

# 5. Broadcast a task across the swarm
coord.dispatch_task({"job": "analyze_data"}, capability="nlp")
```

---

## Repository Sync

`RepositorySync` bridges the running swarm and its GitHub repository using
the **GitHub REST API v3** (no extra dependencies – only the Python standard
library):

```python
from swarm.sync import RepositorySync

sync = RepositorySync(
    repo_url="https://github.com/lippytm/MyClaw.lippytm.AI-",
    token="ghp_...",   # or set GITHUB_TOKEN env variable
)

sync.is_connected()        # → True / False
sync.pull()                # git pull origin main
sync.fetch()               # git fetch origin main
sync.get_latest_commit()   # → {sha, message, author, timestamp}
sync.export_snapshot(coordinator)   # write swarm_snapshot.json
sync.import_snapshot()              # read swarm_snapshot.json
```

Set `GITHUB_TOKEN` as an environment variable to avoid passing the token
explicitly.

---

## Installation

```bash
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest
```

---

## Project Structure

```
MyClaw.lippytm.AI-/
├── swarm/
│   ├── __init__.py
│   ├── agent.py
│   ├── messaging.py
│   ├── network.py
│   ├── coordinator.py
│   └── sync.py
├── tests/
│   ├── test_agent.py
│   ├── test_messaging.py
│   ├── test_network.py
│   ├── test_coordinator.py
│   └── test_sync.py
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## License

Released under the [CC0 1.0 Universal](LICENSE) public domain dedication.

