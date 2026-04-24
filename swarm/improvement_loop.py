from __future__ import annotations

from typing import Dict, List


def summarize_signals(signals: List[Dict[str, str]]) -> Dict[str, object]:
    by_type: Dict[str, int] = {}
    for signal in signals:
        signal_type = signal.get('type', 'unknown')
        by_type[signal_type] = by_type.get(signal_type, 0) + 1
    return {
        'total_signals': len(signals),
        'by_type': by_type,
    }


def recommend_actions(signals: List[Dict[str, str]]) -> List[str]:
    types = {signal.get('type') for signal in signals}
    actions: List[str] = []
    if 'routing_failure' in types:
        actions.append('review swarm routing rules')
    if 'dead_letter_growth' in types:
        actions.append('inspect replay and escalation paths')
    if 'confidence_drop' in types:
        actions.append('raise supervisor review threshold')
    if not actions:
        actions.append('continue monitoring')
    return actions


def build_improvement_summary(signals: List[Dict[str, str]]) -> Dict[str, object]:
    return {
        'summary': summarize_signals(signals),
        'recommended_actions': recommend_actions(signals),
        'next_step': 'governed review',
    }
