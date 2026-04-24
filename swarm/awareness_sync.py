from __future__ import annotations

from typing import Dict, List


def summarize_awareness(items: List[Dict[str, object]]) -> Dict[str, object]:
    by_lane: Dict[str, int] = {}
    for item in items:
        lane = str(item.get('primary_lane', 'unknown'))
        by_lane[lane] = by_lane.get(lane, 0) + 1
    return {
        'total_items': len(items),
        'by_lane': by_lane,
    }


def recommend_sync_actions(items: List[Dict[str, object]]) -> List[str]:
    actions: List[str] = []
    missing = [item for item in items if not item.get('repo') or not item.get('primary_lane')]
    if missing:
        actions.append('repair incomplete awareness records')
    if not actions:
        actions.append('continue awareness sync monitoring')
    return actions


def build_awareness_sync_summary(items: List[Dict[str, object]]) -> Dict[str, object]:
    return {
        'summary': summarize_awareness(items),
        'recommended_actions': recommend_sync_actions(items),
        'next_step': 'governed awareness review',
    }
