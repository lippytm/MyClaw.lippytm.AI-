# Multi-Agent Protocol

This document defines the coordination protocol for agents operating inside the MyClaw swarm fabric.

Its purpose is to make agent collaboration:

- understandable
- predictable
- extensible
- safe enough for mass manufacturing and future scale

---

## Protocol Goals

The protocol should allow agents to:

1. identify themselves clearly
2. advertise capabilities
3. receive tasks with constraints
4. communicate progress and failure
5. escalate when confidence is low
6. hand off work cleanly to other agents
7. generate traceable events for the wider fleet

---

## Core Message Types

| Message Type | Purpose |
|---|---|
| `register` | Announce a new agent to the coordinator |
| `heartbeat` | Confirm liveness and current state |
| `task_offer` | Advertise a task opportunity or request available workers |
| `task_assign` | Assign a task to a target agent |
| `task_accept` | Confirm task acceptance |
| `task_decline` | Reject task because of missing capability, overload, or constraints |
| `task_update` | Report progress |
| `task_complete` | Report successful completion |
| `task_fail` | Report failure |
| `handoff` | Transfer responsibility to another agent |
| `escalate` | Request supervisor or operator involvement |
| `broadcast` | Send a message to many agents |
| `memory_attach` | Attach or reference context for the next agent |

---

## Agent States

| State | Meaning |
|---|---|
| `initializing` | Agent is starting up |
| `online` | Agent is ready for work |
| `busy` | Agent is actively handling a task |
| `paused` | Agent is intentionally not processing work |
| `degraded` | Agent is online but should not receive heavy or sensitive work |
| `offline` | Agent is unavailable |
| `error` | Agent is unhealthy or failed |

---

## Required Agent Identity Fields

Each agent should expose:

```yaml
agent_id: unique-agent-id
name: builder-01
role: builder
capabilities:
  - docs
  - architecture
  - workflow-design
state: online
confidence_profile:
  default: medium
supervisor: supervisor-01
channels:
  - internal
  - openai
  - github
```

---

## Task Envelope

A task passed between agents should include:

```yaml
task_id: task-123
objective: create control tower docs
priority: normal
required_capability: documentation
inputs: {}
constraints:
  write_allowed: true
  review_required: false
  protected_paths: []
  max_cost_usd: 2
success_criteria:
  - file exists
  - content is structurally complete
```

---

## Acceptance Rules

An agent should accept work only if:

- it has the required capability
- it is not overloaded
- the constraints are compatible with its permissions
- confidence is high enough for the task class

If not, the agent should decline or escalate rather than guess unsafely.

---

## Handoff Rules

A handoff should include:

- current task state
- completed work summary
- unresolved questions
- attached memory or references
- reason for handoff

Handoffs are preferred over silent abandonment.

---

## Escalation Rules

Escalate when:

- required capability is missing
- confidence is below threshold
- policy requires review or approval
- a protected path is involved
- repeated failures occur
- downstream systems are unclear or inconsistent

Escalation targets can include:
- supervisor agent
- control tower
- human operator

---

## Memory Handoff

Agents should not assume perfect persistent memory.

A memory handoff should record:

- task summary
- decisions made
- files touched
- assumptions used
- next recommended action

This keeps the swarm resilient across interruptions and future expansion.

---

## Reliability Rules

The protocol should favor:

- explicit acknowledgements
- structured status updates
- recoverable failure reporting
- replayable events
- minimal ambiguity in task ownership

---

## Suggested Lifecycle

1. agent registers
2. agent sends heartbeats
3. coordinator offers or assigns task
4. agent accepts or declines
5. agent reports updates
6. agent completes, fails, hands off, or escalates
7. coordinator records outcome and routes next action

---

## Rule of thumb

A swarm becomes scalable when agents do not merely act. They identify themselves clearly, accept work deliberately, report status transparently, and hand off responsibility without losing context.
