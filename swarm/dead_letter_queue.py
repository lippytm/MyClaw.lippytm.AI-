from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


@dataclass
class DeadLetterRecord:
    task_id: str
    reason: str
    payload: Dict[str, Any]
    failure_count: int = 1
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    last_error: Optional[str] = None
    replayable: bool = True
    tags: List[str] = field(default_factory=list)


class DeadLetterQueue:
    def __init__(self) -> None:
        self._records: Dict[str, DeadLetterRecord] = {}

    def add(self, task_id: str, reason: str, payload: Dict[str, Any], error: Optional[str] = None, tags: Optional[List[str]] = None) -> DeadLetterRecord:
        if task_id in self._records:
            record = self._records[task_id]
            record.failure_count += 1
            record.reason = reason
            record.payload = payload
            record.last_error = error
            if tags:
                record.tags = sorted(set(record.tags + tags))
            return record

        record = DeadLetterRecord(
            task_id=task_id,
            reason=reason,
            payload=payload,
            last_error=error,
            tags=tags or [],
        )
        self._records[task_id] = record
        return record

    def get(self, task_id: str) -> Optional[DeadLetterRecord]:
        return self._records.get(task_id)

    def list_all(self) -> List[DeadLetterRecord]:
        return list(self._records.values())

    def mark_not_replayable(self, task_id: str) -> Optional[DeadLetterRecord]:
        record = self.get(task_id)
        if record:
            record.replayable = False
        return record

    def replay_candidates(self) -> List[DeadLetterRecord]:
        return [record for record in self._records.values() if record.replayable]

    def remove(self, task_id: str) -> bool:
        return self._records.pop(task_id, None) is not None
