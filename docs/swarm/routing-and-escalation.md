# Routing and Escalation

This document defines how tasks should be routed through the MyClaw swarm and when the system should escalate to supervisors, control systems, or human operators.

The routing model should support:

- specialization
- flexibility
- explainability
- failure recovery
- controlled scale

---

## Routing Goals

A good routing decision sends the right work to the right agent at the right time with the right constraints.

Routing should optimize for:

1. capability fit
2. confidence fit
3. workload balance
4. policy compliance
5. cost awareness
6. recovery readiness

---

## Routing Inputs

The coordinator should consider:

- required capability
- task priority
- path sensitivity
- policy constraints
- current agent state
- recent agent success rate
- current workload
- estimated cost or effort
- escalation history

---

## Suggested Routing Order

### Step 1 — Filter by capability
Only consider agents that advertise the required capability.

### Step 2 — Filter by eligibility
Remove agents that are:
- offline
- paused
- overloaded
- blocked by policy constraints

### Step 3 — Score candidates
Suggested score components:
- capability match
- confidence level
- recent reliability
- queue depth
- routing cost
- supervisor preference

### Step 4 — Assign or escalate
If one or more qualified candidates remain, assign to the highest-scoring candidate.
If not, escalate.

---

## Example Routing Score Model

```text
score =
  capability_match * 40
+ confidence_score * 20
+ reliability_score * 15
+ workload_score * 10
+ policy_fit * 10
+ cost_efficiency * 5
```

This weighting can be tuned over time.

---

## Escalation Levels

| Level | Target | When to use |
|---|---|---|
| `L1` | peer agent | Another capable agent may handle the task better |
| `L2` | supervisor agent | Ambiguity, repeated decline, or low-confidence handling |
| `L3` | control tower | Multi-repo, governed, or rollout-related decisions |
| `L4` | human operator | Sensitive approvals, repeated failure, or unclear intent |

---

## Escalation Triggers

Escalate when:

- no eligible agent exists
- confidence is below threshold
- task affects protected paths
- task spans multiple repos or systems
- task has failed more than allowed retry count
- conflicting outputs appear
- policy outcome is `review`, `approve`, or `block`

---

## Retry Strategy

Recommended retry model:

1. retry same agent once if failure is transient
2. reroute to another capable agent if retry fails
3. escalate to supervisor if candidate quality drops below threshold
4. escalate to control tower or human if policy-sensitive or repeated failure continues

Retries should not be infinite.

---

## Dead-Letter Conditions

A task should move to dead-letter or incident review if:

- repeated attempts fail
- required capability cannot be satisfied
- required approvals never arrive
- the payload is malformed or incomplete
- routing loops are detected

Dead-letter tasks should remain inspectable and replayable.

---

## Human Override

A human operator should be able to:

- force assignment to a specific agent
- pause an agent class
- block a task
- approve protected execution
- re-open a dead-letter task
- override routing weights for special cases

---

## Routing Profiles

### Fast Mode
Use when speed matters more than optimal scoring.

### Balanced Mode
Default mode for most internal tasks.

### Safe Mode
Prefer strict policy and supervisor review over speed.

### Manufacturing Mode
Use for repeated, templated tasks across many repos with pre-approved patterns.

---

## Manufacturing Mode Guidance

Manufacturing mode is appropriate when:

- tasks follow a known template
- target folders are predictable
- policy classification is already known
- expected outputs are structured
- rollback is easy

Examples:
- bootstrap docs across repos
- standard folder additions
- policy propagation
- schema rollout

---

## Observability for Routing

Track at least:

- assignment count by agent
- decline rate
- escalation rate
- retry count
- completion rate
- dead-letter count
- average completion time

These metrics help evolve the swarm rather than guess about its performance.

---

## Rule of thumb

The swarm should route work the way a strong engineering organization does: by matching the problem to the best available specialist, knowing when to ask for help, and preserving enough context that failure becomes learning instead of confusion.
