# MyClaw.lippytm.AI — AI Swarm Communications & Networking Management System

A cross-platform, cross-channel framework for coordinating fleets of AI agents through a unified communications and networking layer.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     SwarmCoordinator                        │
│  ┌──────────────────────┐  ┌───────────────────────────┐   │
│  │     MessageBus        │  │     NetworkTopology        │   │
│  │  ┌────────────────┐  │  │  ┌─────────────────────┐  │   │
│  │  │ Unicast        │  │  │  │ Nodes (agents)       │  │   │
│  │  │ Broadcast      │  │  │  │ Directed links        │  │   │
│  │  │ Pub / Sub      │  │  │  │ BFS path-finding      │  │   │
│  │  └────────────────┘  │  │  └─────────────────────┘  │   │
│  └──────────────────────┘  └───────────────────────────┘   │
│                                                             │
│  Agent  Agent  Agent  …  (unlimited online nodes)           │
└─────────────────────────────────────────────────────────────┘
```

### Core modules

| Module | Responsibility |
|---|---|
| `swarm/agent.py` | Individual AI node: identity, capabilities, status, inbox |
| `swarm/messaging.py` | `Message` dataclass + `MessageBus` (unicast, broadcast, pub/sub) |
| `swarm/network.py` | `NetworkTopology` — directed graph of links, BFS path-finding |
| `swarm/coordinator.py` | `SwarmCoordinator` — orchestrates agents, routing, task dispatch |

---

## Quick Start

```python
from swarm import SwarmCoordinator, Agent, MessageType

# 1. Create the coordinator
coordinator = SwarmCoordinator()

# 2. Register agents with capabilities
nlp_agent    = Agent("NLP-Worker",    capabilities=["nlp"])
vision_agent = Agent("Vision-Worker", capabilities=["vision"])
coordinator.register_agent(nlp_agent)
coordinator.register_agent(vision_agent, connect_to=[nlp_agent.agent_id])

# 3. Dispatch a task to the best capable agent
target_id = coordinator.dispatch_task(
    task_payload={"query": "Translate this text"},
    required_capability="nlp",
)
print(f"Task dispatched to: {target_id}")

# 4. Unicast message
coordinator.send_message(
    sender_id=nlp_agent.agent_id,
    receiver_id=vision_agent.agent_id,
    message_type=MessageType.DATA,
    payload={"result": "Translation complete"},
)

# 5. Broadcast a heartbeat
coordinator.send_heartbeat()

# 6. Publish to a topic (pub/sub)
coordinator.subscribe_agent_to_topic(vision_agent.agent_id, "alerts")
coordinator.publish_to_topic("alerts", payload={"level": "warning", "msg": "Low memory"})

# 7. Network path-finding
coordinator.add_network_link(nlp_agent.agent_id, vision_agent.agent_id)
path = coordinator.find_route(nlp_agent.agent_id, vision_agent.agent_id)
print(f"Route: {path}")

# 8. Swarm health
print(coordinator.get_swarm_status())
```

---

## Messaging Modes

| Mode | API | Description |
|---|---|---|
| Unicast | `bus.send(message)` | Deliver to a single named agent |
| Broadcast | `bus.broadcast(message)` | Deliver to all agents (except sender) |
| Pub / Sub | `bus.publish(message)` | Deliver to topic subscribers + handlers |

---

## Network Topology

`NetworkTopology` maintains a **directed graph** of agent nodes and their
links.  Key features:

* Add / remove nodes and directed links at runtime.
* Mark links active or inactive without removing them.
* **BFS shortest-path** routing: `find_path(source, target)` returns the
  minimum-hop route through active links only.
* Network summary with node/link counts.

---

## Agent Lifecycle

```
INITIALIZING → ONLINE ⇄ BUSY
                  ↓
               OFFLINE
                  ↓
               ERROR
```

Agents expose a typed capability list used by `SwarmCoordinator` for
intelligent task routing.

---

## Running Tests

```bash
pip install pytest
pytest
```

All 91 tests should pass.

