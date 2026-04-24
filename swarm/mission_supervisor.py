from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List


@dataclass
class MissionStatus:
    mission_id: str
    state: str = 'queued'
    completed_tasks: List[str] = field(default_factory=list)
    failed_tasks: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)


class MissionSupervisor:
    def __init__(self) -> None:
        self._missions: Dict[str, MissionStatus] = {}

    def start(self, mission_id: str) -> MissionStatus:
        status = MissionStatus(mission_id=mission_id, state='running')
        self._missions[mission_id] = status
        return status

    def complete_task(self, mission_id: str, task_id: str) -> MissionStatus:
        status = self._missions.setdefault(mission_id, MissionStatus(mission_id=mission_id))
        status.completed_tasks.append(task_id)
        return status

    def fail_task(self, mission_id: str, task_id: str, note: str = '') -> MissionStatus:
        status = self._missions.setdefault(mission_id, MissionStatus(mission_id=mission_id))
        status.failed_tasks.append(task_id)
        if note:
            status.notes.append(note)
        status.state = 'review'
        return status

    def summarize(self, mission_id: str) -> Dict[str, object]:
        status = self._missions.get(mission_id)
        if not status:
            return {'mission_id': mission_id, 'state': 'unknown'}
        return {
            'mission_id': status.mission_id,
            'state': status.state,
            'completed_count': len(status.completed_tasks),
            'failed_count': len(status.failed_tasks),
            'notes': status.notes,
        }
