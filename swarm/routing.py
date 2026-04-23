from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Optional


@dataclass
class RoutingCandidate:
    agent_id: str
    capabilities: List[str] = field(default_factory=list)
    state: str = "online"
    confidence: float = 0.75
    reliability: float = 0.75
    workload: int = 0
    supervisor_preferred: bool = False
    cost_score: float = 0.5


@dataclass
class RoutingDecision:
    selected_agent_id: Optional[str]
    status: str
    score_breakdown: Dict[str, float] = field(default_factory=dict)
    considered_agents: List[str] = field(default_factory=list)
    escalation_required: bool = False
    reason: str = ""


class TaskRouter:
    def __init__(self, overload_threshold: int = 5, confidence_threshold: float = 0.55):
        self.overload_threshold = overload_threshold
        self.confidence_threshold = confidence_threshold

    def _eligible(self, candidate: RoutingCandidate, required_capability: str) -> bool:
        if candidate.state not in {"online", "busy"}:
            return False
        if required_capability not in candidate.capabilities:
            return False
        if candidate.workload > self.overload_threshold:
            return False
        return True

    def _score(self, candidate: RoutingCandidate, required_capability: str) -> Dict[str, float]:
        capability_match = 40.0 if required_capability in candidate.capabilities else 0.0
        confidence_score = max(0.0, min(candidate.confidence, 1.0)) * 20.0
        reliability_score = max(0.0, min(candidate.reliability, 1.0)) * 15.0
        workload_score = max(0.0, (1 - min(candidate.workload / max(self.overload_threshold, 1), 1.0))) * 10.0
        supervisor_bonus = 10.0 if candidate.supervisor_preferred else 5.0
        cost_efficiency = max(0.0, min(candidate.cost_score, 1.0)) * 5.0
        total = capability_match + confidence_score + reliability_score + workload_score + supervisor_bonus + cost_efficiency
        return {
            "capability_match": capability_match,
            "confidence_score": confidence_score,
            "reliability_score": reliability_score,
            "workload_score": workload_score,
            "policy_fit": supervisor_bonus,
            "cost_efficiency": cost_efficiency,
            "total": total,
        }

    def route(
        self,
        task: Dict[str, Any],
        candidates: Iterable[RoutingCandidate],
    ) -> RoutingDecision:
        required_capability = task.get("required_capability") or "general"
        priority = task.get("priority", "normal")
        candidate_list = list(candidates)
        eligible = [c for c in candidate_list if self._eligible(c, required_capability)]

        if not eligible:
            return RoutingDecision(
                selected_agent_id=None,
                status="escalate",
                considered_agents=[c.agent_id for c in candidate_list],
                escalation_required=True,
                reason=f"No eligible agents found for capability '{required_capability}'.",
            )

        scored = [(c, self._score(c, required_capability)) for c in eligible]
        scored.sort(key=lambda item: item[1]["total"], reverse=True)
        best_candidate, best_scores = scored[0]

        if best_candidate.confidence < self.confidence_threshold and priority in {"high", "critical"}:
            return RoutingDecision(
                selected_agent_id=best_candidate.agent_id,
                status="escalate",
                score_breakdown=best_scores,
                considered_agents=[c.agent_id for c, _ in scored],
                escalation_required=True,
                reason="Best candidate is below confidence threshold for sensitive work.",
            )

        return RoutingDecision(
            selected_agent_id=best_candidate.agent_id,
            status="assigned",
            score_breakdown=best_scores,
            considered_agents=[c.agent_id for c, _ in scored],
            escalation_required=False,
            reason="Task routed to highest scoring eligible candidate.",
        )
