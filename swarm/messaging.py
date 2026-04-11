"""
AI Swarm Messaging module.

Provides the :class:`Message` data-class and the :class:`MessageBus` that
routes messages between agents using unicast, broadcast, and topic-based
(pub/sub) delivery modes.
"""

from __future__ import annotations

import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Set

if TYPE_CHECKING:
    from .agent import Agent


class MessageType(Enum):
    """Semantic type of a swarm message."""

    COMMAND = "command"          # Instruction to execute an action
    DATA = "data"                # Payload carrying information
    STATUS = "status"            # Agent/network status update
    HEARTBEAT = "heartbeat"      # Liveness ping
    BROADCAST = "broadcast"      # One-to-all message
    TASK_REQUEST = "task_request"    # Request for task execution
    TASK_RESPONSE = "task_response"  # Result of a task execution
    ERROR = "error"              # Error notification


@dataclass
class Message:
    """Immutable message exchanged between agents.

    Attributes:
        sender_id: ``agent_id`` of the originating agent
            (``"system"`` for infrastructure messages).
        receiver_id: ``agent_id`` of the target agent, or ``None`` for
            broadcast / topic messages.
        message_type: Semantic :class:`MessageType`.
        payload: Arbitrary application data.
        message_id: Auto-generated UUID.
        timestamp: UTC creation time.
        topic: Optional pub/sub topic name.
        correlation_id: Links a response to a prior request.
        metadata: Arbitrary key/value pairs.
    """

    sender_id: str
    receiver_id: Optional[str]
    message_type: MessageType
    payload: Any = None
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    topic: Optional[str] = None
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialise the message to a plain dictionary."""
        return {
            "message_id": self.message_id,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "message_type": self.message_type.value,
            "payload": self.payload,
            "timestamp": self.timestamp.isoformat(),
            "topic": self.topic,
            "correlation_id": self.correlation_id,
            "metadata": dict(self.metadata),
        }


class MessageBus:
    """Central message broker for the swarm.

    Supports three delivery modes:

    * **Unicast** – ``send(message)`` routes a message to a single agent.
    * **Broadcast** – ``broadcast(message)`` delivers to *all* registered
      agents (excluding the sender).
    * **Topic pub/sub** – agents subscribe to named topics via
      :meth:`subscribe`; senders use :meth:`publish`.

    All operations are thread-safe.
    """

    def __init__(self) -> None:
        self._agents: Dict[str, Agent] = {}
        self._topic_subscribers: Dict[str, Set[str]] = {}
        self._message_log: List[Message] = []
        self._lock = threading.RLock()
        self._topic_handlers: Dict[str, List[Callable[[Message], None]]] = {}

    # ------------------------------------------------------------------
    # Agent registration
    # ------------------------------------------------------------------

    def register_agent(self, agent: Agent) -> None:
        """Register *agent* with the bus so it can receive messages."""
        with self._lock:
            self._agents[agent.agent_id] = agent

    def unregister_agent(self, agent_id: str) -> None:
        """Remove an agent from the bus and all its topic subscriptions."""
        with self._lock:
            self._agents.pop(agent_id, None)
            for subscribers in self._topic_subscribers.values():
                subscribers.discard(agent_id)

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Return the agent with *agent_id*, or ``None``."""
        with self._lock:
            return self._agents.get(agent_id)

    def list_agents(self) -> List[Agent]:
        """Return a snapshot of all registered agents."""
        with self._lock:
            return list(self._agents.values())

    # ------------------------------------------------------------------
    # Unicast
    # ------------------------------------------------------------------

    def send(self, message: Message) -> bool:
        """Deliver *message* to its designated recipient.

        Returns:
            ``True`` on successful delivery, ``False`` when the target
            agent is not registered.
        """
        with self._lock:
            agent = self._agents.get(message.receiver_id)  # type: ignore[arg-type]
        if agent is None:
            return False
        agent.deliver(message)
        self._log(message)
        return True

    # ------------------------------------------------------------------
    # Broadcast
    # ------------------------------------------------------------------

    def broadcast(self, message: Message) -> int:
        """Deliver *message* to every registered agent except the sender.

        Returns:
            The number of agents that received the message.
        """
        with self._lock:
            targets = [
                a
                for a in self._agents.values()
                if a.agent_id != message.sender_id
            ]
        for agent in targets:
            agent.deliver(message)
        self._log(message)
        return len(targets)

    # ------------------------------------------------------------------
    # Pub / Sub
    # ------------------------------------------------------------------

    def subscribe(self, agent_id: str, topic: str) -> None:
        """Subscribe *agent_id* to *topic*."""
        with self._lock:
            self._topic_subscribers.setdefault(topic, set()).add(agent_id)

    def unsubscribe(self, agent_id: str, topic: str) -> None:
        """Remove *agent_id*'s subscription to *topic*."""
        with self._lock:
            if topic in self._topic_subscribers:
                self._topic_subscribers[topic].discard(agent_id)

    def subscribe_handler(
        self, topic: str, handler: Callable[[Message], None]
    ) -> None:
        """Register a callable invoked when a message is published to *topic*.

        Unlike :meth:`subscribe`, this does not require an agent to be
        registered on the bus; it is useful for system-level listeners.
        """
        with self._lock:
            self._topic_handlers.setdefault(topic, []).append(handler)

    def publish(self, message: Message) -> int:
        """Publish *message* to its topic.

        Delivers to all subscribing agents and all topic handlers.

        Returns:
            Total number of deliveries made.
        """
        if message.topic is None:
            raise ValueError("Cannot publish a message without a topic.")
        with self._lock:
            subscriber_ids = set(
                self._topic_subscribers.get(message.topic, set())
            )
            agents = {
                aid: self._agents[aid]
                for aid in subscriber_ids
                if aid in self._agents
            }
            handlers = list(
                self._topic_handlers.get(message.topic, [])
            )
        count = 0
        for agent in agents.values():
            agent.deliver(message)
            count += 1
        for handler in handlers:
            handler(message)
            count += 1
        self._log(message)
        return count

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    def _log(self, message: Message) -> None:
        with self._lock:
            self._message_log.append(message)

    def get_message_log(self) -> List[Message]:
        """Return an immutable snapshot of all routed messages."""
        with self._lock:
            return list(self._message_log)

    def clear_log(self) -> None:
        """Clear the message log."""
        with self._lock:
            self._message_log.clear()

    # ------------------------------------------------------------------
    # Introspection
    # ------------------------------------------------------------------

    def get_topic_subscribers(self, topic: str) -> List[str]:
        """Return the list of agent IDs subscribed to *topic*."""
        with self._lock:
            return list(self._topic_subscribers.get(topic, set()))
