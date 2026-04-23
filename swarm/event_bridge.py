from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class RoutedEvent:
    event_type: str
    source_repo: str
    target_component: str
    payload: Dict[str, Any]
    route_hint: str = "standard"


def event_to_routing_task(event: Dict[str, Any]) -> Dict[str, Any]:
    payload = event.get("payload", {})
    event_type = event.get("event_type", "task.created")

    capability_map = {
        "billing.event": "commerce",
        "task.created": "routing",
        "lead.created": "intake",
        "content.generated": "knowledge",
    }

    return {
        "task_id": payload.get("taskId") or payload.get("task_id") or f"evt_task_{event.get('event_id', 'unknown')}",
        "objective": payload.get("objective") or f"Handle event: {event_type}",
        "required_capability": capability_map.get(event_type, "general"),
        "priority": event.get("priority", "normal"),
        "context": {
            "event_type": event_type,
            "source": event.get("source", {}),
            "target": event.get("target", {}),
        },
        "constraints": {
            "write_allowed": False,
            "review_required": False,
            "protected_paths": [],
        },
    }
