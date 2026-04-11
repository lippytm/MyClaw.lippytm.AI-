"""
swarm/messaging.py – Cross-channel messaging for the MyClaw Swarm System.

Provides:
  • Message  – lightweight message data class
  • MessageBus – pub/sub broker that routes messages to subscribed Agents
"""

from __future__ import annotations

import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from swarm.agent import Agent

logger = logging.getLogger(__name__)


class Message:
    """An immutable message passed between agents.

    Attributes:
        message_id: Unique identifier.
        topic: Routing topic / channel name.
        payload: Arbitrary payload data.
        sender_id: Agent id of the sender (optional).
        timestamp: UTC creation time.
    """

    def __init__(
        self,
        topic: str,
        payload: object,
        sender_id: Optional[str] = None,
        message_id: Optional[str] = None,
    ) -> None:
        self.message_id: str = message_id or str(uuid.uuid4())
        self.topic: str = topic
        self.payload: object = payload
        self.sender_id: Optional[str] = sender_id
        self.timestamp: datetime = datetime.now(tz=timezone.utc)

    def to_dict(self) -> dict:
        """Serialise to a plain dictionary."""
        return {
            "message_id": self.message_id,
            "topic": self.topic,
            "payload": self.payload,
            "sender_id": self.sender_id,
            "timestamp": self.timestamp.isoformat(),
        }

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"Message(topic={self.topic!r}, sender={self.sender_id!r}, "
            f"id={self.message_id!r})"
        )


class MessageBus:
    """A simple in-process pub/sub message bus.

    Agents subscribe to topics.  When a message is published on a topic,
    every subscribed agent's ``receive()`` method is called with the message
    dictionary.
    """

    def __init__(self) -> None:
        self._subscriptions: Dict[str, List["Agent"]] = {}
        self._history: List[Message] = []
        logger.info("MessageBus initialised.")

    # ------------------------------------------------------------------
    # Subscription management
    # ------------------------------------------------------------------

    def subscribe(self, topic: str, agent: "Agent") -> None:
        """Subscribe *agent* to *topic*."""
        self._subscriptions.setdefault(topic, [])
        if agent not in self._subscriptions[topic]:
            self._subscriptions[topic].append(agent)
            logger.debug(
                "Agent '%s' subscribed to topic '%s'.", agent.name, topic
            )

    def unsubscribe(self, topic: str, agent: "Agent") -> None:
        """Unsubscribe *agent* from *topic* (no-op if not subscribed)."""
        subscribers = self._subscriptions.get(topic, [])
        if agent in subscribers:
            subscribers.remove(agent)
            logger.debug(
                "Agent '%s' unsubscribed from topic '%s'.", agent.name, topic
            )

    # ------------------------------------------------------------------
    # Publishing
    # ------------------------------------------------------------------

    def publish(self, message: Message) -> int:
        """Publish *message* to all subscribers of its topic.

        Returns:
            Number of agents that received the message.
        """
        self._history.append(message)
        subscribers = self._subscriptions.get(message.topic, [])
        count = 0
        for agent in subscribers:
            agent.receive(message.to_dict())
            count += 1
        logger.debug(
            "Published message id=%s on topic '%s' to %d agent(s).",
            message.message_id,
            message.topic,
            count,
        )
        return count

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    def topics(self) -> List[str]:
        """Return list of all topics that have at least one subscriber."""
        return [t for t, subs in self._subscriptions.items() if subs]

    def history(self, topic: Optional[str] = None) -> List[Message]:
        """Return message history, optionally filtered by topic."""
        if topic is None:
            return list(self._history)
        return [m for m in self._history if m.topic == topic]

    def __repr__(self) -> str:  # pragma: no cover
        return f"MessageBus(topics={self.topics()!r})"
