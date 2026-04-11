"""
AI Swarm Agent module.

Represents an individual AI node participating in the swarm network.
Each agent has a unique identity, a set of capabilities, and a status,
and communicates through the swarm's message-bus.
"""

from __future__ import annotations

import threading
import uuid
from collections import deque
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Deque, Dict, List, Optional

if TYPE_CHECKING:
    from .messaging import Message


class AgentStatus(Enum):
    """Lifecycle states of a swarm agent."""

    INITIALIZING = "initializing"
    ONLINE = "online"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"


class Agent:
    """An individual AI agent (node) in the swarm.

    Attributes:
        agent_id: Globally unique identifier for this agent.
        name: Human-readable label.
        capabilities: List of capability tags (e.g. ``["nlp", "vision"]``).
        status: Current :class:`AgentStatus`.
        metadata: Arbitrary key/value pairs for extra information.
    """

    def __init__(
        self,
        name: str,
        capabilities: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        agent_id: Optional[str] = None,
    ) -> None:
        self.agent_id: str = agent_id or str(uuid.uuid4())
        self.name: str = name
        self.capabilities: List[str] = capabilities or []
        self.metadata: Dict[str, Any] = metadata or {}
        self.status: AgentStatus = AgentStatus.INITIALIZING

        # Inbox stores messages delivered to this agent
        self._inbox: Deque[Message] = deque()
        self._inbox_lock = threading.Lock()

        # Optional application-level message handler
        self._message_handler: Optional[Callable[[Message], None]] = None

    # ------------------------------------------------------------------
    # Status helpers
    # ------------------------------------------------------------------

    def set_online(self) -> None:
        """Mark the agent as online and ready."""
        self.status = AgentStatus.ONLINE

    def set_offline(self) -> None:
        """Mark the agent as offline."""
        self.status = AgentStatus.OFFLINE

    def set_busy(self) -> None:
        """Mark the agent as busy processing a task."""
        self.status = AgentStatus.BUSY

    def set_error(self) -> None:
        """Mark the agent as being in an error state."""
        self.status = AgentStatus.ERROR

    @property
    def is_available(self) -> bool:
        """Return ``True`` when the agent can accept new tasks/messages."""
        return self.status == AgentStatus.ONLINE

    # ------------------------------------------------------------------
    # Capability helpers
    # ------------------------------------------------------------------

    def has_capability(self, capability: str) -> bool:
        """Return ``True`` if the agent supports *capability*."""
        return capability in self.capabilities

    def add_capability(self, capability: str) -> None:
        """Register a new capability with this agent."""
        if capability not in self.capabilities:
            self.capabilities.append(capability)

    def remove_capability(self, capability: str) -> None:
        """Remove a capability from this agent."""
        self.capabilities = [c for c in self.capabilities if c != capability]

    # ------------------------------------------------------------------
    # Messaging
    # ------------------------------------------------------------------

    def set_message_handler(self, handler: Callable[[Message], None]) -> None:
        """Register an application-level callback invoked on each delivery."""
        self._message_handler = handler

    def deliver(self, message: Message) -> None:
        """Deliver *message* to this agent's inbox (thread-safe).

        If a message handler is registered it is called immediately.
        """
        with self._inbox_lock:
            self._inbox.append(message)
        if self._message_handler is not None:
            self._message_handler(message)

    def receive(self) -> Optional[Message]:
        """Pop and return the oldest message from the inbox, or ``None``."""
        with self._inbox_lock:
            return self._inbox.popleft() if self._inbox else None

    def inbox_size(self) -> int:
        """Return the number of pending messages in the inbox."""
        with self._inbox_lock:
            return len(self._inbox)

    # ------------------------------------------------------------------
    # Dunder helpers
    # ------------------------------------------------------------------

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"Agent(id={self.agent_id!r}, name={self.name!r}, "
            f"status={self.status.value!r})"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Serialise the agent to a plain dictionary."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "capabilities": list(self.capabilities),
            "status": self.status.value,
            "metadata": dict(self.metadata),
        }
