from __future__ import annotations

from typing import Dict, Optional
from datetime import datetime, timezone


class StateTracker:
    def __init__(self) -> None:
        self._states: Dict[str, Dict[str, object]] = {}

    def update(
        self,
        system_id: str,
        lane: str,
        state: str,
        confidence: float = 0.75,
        mission_id: Optional[str] = None,
    ) -> Dict[str, object]:
        snapshot = {
            'system_id': system_id,
            'lane': lane,
            'state': state,
            'confidence': confidence,
            'current_mission_id': mission_id,
            'updated_at': datetime.now(timezone.utc).isoformat(),
        }
        self._states[system_id] = snapshot
        return snapshot

    def get(self, system_id: str) -> Optional[Dict[str, object]]:
        return self._states.get(system_id)

    def summary(self) -> Dict[str, object]:
        by_lane: Dict[str, int] = {}
        for state in self._states.values():
            lane = str(state.get('lane', 'unknown'))
            by_lane[lane] = by_lane.get(lane, 0) + 1
        return {
            'total_systems': len(self._states),
            'by_lane': by_lane,
            'active_missions': sum(1 for state in self._states.values() if state.get('current_mission_id')),
        }
