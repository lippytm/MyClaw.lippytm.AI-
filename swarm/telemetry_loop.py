from __future__ import annotations

from typing import Dict, List


def summarize_telemetry(events: List[Dict[str, str]]) -> Dict[str, object]:
    by_type: Dict[str, int] = {}
    for event in events:
        event_type = event.get('type', 'unknown')
        by_type[event_type] = by_type.get(event_type, 0) + 1
    return {
        'total_events': len(events),
        'by_type': by_type,
    }


def recommend_telemetry_actions(events: List[Dict[str, str]]) -> List[str]:
    types = {event.get('type') for event in events}
    actions: List[str] = []
    if 'missing_event' in types:
        actions.append('add missing event emission')
    if 'stale_state' in types:
        actions.append('refresh state reporting path')
    if not actions:
        actions.append('continue telemetry monitoring')
    return actions


def build_telemetry_summary(events: List[Dict[str, str]]) -> Dict[str, object]:
    return {
        'summary': summarize_telemetry(events),
        'recommended_actions': recommend_telemetry_actions(events),
        'next_step': 'governed telemetry review',
    }
