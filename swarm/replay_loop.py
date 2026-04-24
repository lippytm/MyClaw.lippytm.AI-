from __future__ import annotations

from typing import Dict, List


def summarize_replay(records: List[Dict[str, object]]) -> Dict[str, object]:
    replayable = sum(1 for record in records if record.get('replayable'))
    blocked = len(records) - replayable
    return {
        'total_records': len(records),
        'replayable_records': replayable,
        'blocked_records': blocked,
    }


def recommend_replay_actions(records: List[Dict[str, object]]) -> List[str]:
    summary = summarize_replay(records)
    actions: List[str] = []
    if summary['replayable_records'] > 0:
        actions.append('review replay queue')
    if summary['blocked_records'] > 0:
        actions.append('inspect blocked replay causes')
    if not actions:
        actions.append('continue replay monitoring')
    return actions


def build_replay_summary(records: List[Dict[str, object]]) -> Dict[str, object]:
    return {
        'summary': summarize_replay(records),
        'recommended_actions': recommend_replay_actions(records),
        'next_step': 'governed replay review',
    }
