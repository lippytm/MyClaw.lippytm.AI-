"""
swarm/agent.py – AI Agent for the MyClaw Swarm Communications System.

Each Agent represents an autonomous unit capable of sending and receiving
messages, joining networks, and being coordinated by a Coordinator.
"""

from __future__ import annotations

import uuid
import logging
from typing import Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


class Agent:
    """An autonomous AI agent that participates in a swarm network.

    Attributes:
        agent_id: Unique identifier for this agent.
        name: Human-readable name for this agent.
        capabilities: List of capability tags describing what the agent can do.
        _handlers: Mapping of message topic → handler callable.
    """

    def __init__(
        self,
        name: str,
        capabilities: Optional[List[str]] = None,
        agent_id: Optional[str] = None,
    ) -> None:
        self.agent_id: str = agent_id or str(uuid.uuid4())
        self.name: str = name
        self.capabilities: List[str] = capabilities or []
        self._handlers: Dict[str, Callable] = {}
        self._inbox: List[dict] = []
        logger.info("Agent '%s' (%s) initialised.", self.name, self.agent_id)

    # ------------------------------------------------------------------
    # Handler registration
    # ------------------------------------------------------------------

    def register_handler(self, topic: str, handler: Callable[[dict], None]) -> None:
        """Register a callable to handle incoming messages for *topic*."""
        self._handlers[topic] = handler
        logger.debug("Agent '%s' registered handler for topic '%s'.", self.name, topic)

    # ------------------------------------------------------------------
    # Message processing
    # ------------------------------------------------------------------

    def receive(self, message: dict) -> None:
        """Receive an incoming message and dispatch to its handler (if any).

        Args:
            message: A dict with at least ``topic`` and ``payload`` keys.
        """
        self._inbox.append(message)
        topic = message.get("topic", "")
        handler = self._handlers.get(topic)
        if handler:
            try:
                handler(message)
            except Exception as exc:  # pragma: no cover
                logger.error(
                    "Agent '%s' handler for topic '%s' raised: %s",
                    self.name,
                    topic,
                    exc,
                )
        else:
            logger.debug(
                "Agent '%s' received message for unhandled topic '%s'.",
                self.name,
                topic,
            )

    # ------------------------------------------------------------------
    # Representation
    # ------------------------------------------------------------------

    def status(self) -> dict:
        """Return a status snapshot of this agent."""
        return {
            "agent_id": self.agent_id,
            "name": self.name,
            "capabilities": list(self.capabilities),
            "inbox_size": len(self._inbox),
        }

    def __repr__(self) -> str:  # pragma: no cover
        return f"Agent(name={self.name!r}, id={self.agent_id!r})"
