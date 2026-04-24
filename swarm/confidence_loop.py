from __future__ import annotations

from typing import Dict, List


def summarize_confidence(values: List[float]) -> Dict[str, object]:
    if not values:
        return {'count': 0, 'average': 0.0, 'lowest': 0.0}
    return {
        'count': len(values),
        'average': sum(values) / len(values),
        'lowest': min(values),
    }


def recommend_confidence_actions(values: List[float], threshold: float = 0.6) -> List[str]:
    summary = summarize_confidence(values)
    actions: List[str] = []
    if summary['count'] == 0:
        actions.append('collect confidence signals')
        return actions
    if summary['average'] < threshold:
        actions.append('raise supervisor review frequency')
    if summary['lowest'] < threshold / 2:
        actions.append('inspect low-confidence task classes')
    if not actions:
        actions.append('continue confidence monitoring')
    return actions


def build_confidence_summary(values: List[float]) -> Dict[str, object]:
    return {
        'summary': summarize_confidence(values),
        'recommended_actions': recommend_confidence_actions(values),
        'next_step': 'governed confidence review',
    }
