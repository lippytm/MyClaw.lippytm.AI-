"""
swarm/network.py – Network management for the MyClaw Swarm System.

A Network is a logical grouping of Agents that share a MessageBus.
It tracks membership, routes messages, and exposes connectivity helpers.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, TYPE_CHECKING

from swarm.messaging import Message, MessageBus

if TYPE_CHECKING:
    from swarm.agent import Agent

logger = logging.getLogger(__name__)


class Network:
    """A logical network of agents sharing a message bus.

    Attributes:
        network_id: Unique name / identifier for this network.
        bus: The underlying :class:`~swarm.messaging.MessageBus`.
    """

    def __init__(self, network_id: str) -> None:
        self.network_id: str = network_id
        self.bus: MessageBus = MessageBus()
        self._agents: Dict[str, "Agent"] = {}
        logger.info("Network '%s' created.", self.network_id)

    # ------------------------------------------------------------------
    # Agent membership
    # ------------------------------------------------------------------

    def add_agent(self, agent: "Agent") -> None:
        """Add *agent* to this network and auto-subscribe it to the network topic."""
        self._agents[agent.agent_id] = agent
        self.bus.subscribe(self.network_id, agent)
        logger.debug(
            "Agent '%s' joined network '%s'.", agent.name, self.network_id
        )

    def remove_agent(self, agent: "Agent") -> None:
        """Remove *agent* from this network."""
        self._agents.pop(agent.agent_id, None)
        self.bus.unsubscribe(self.network_id, agent)
        logger.debug(
            "Agent '%s' left network '%s'.", agent.name, self.network_id
        )

    # ------------------------------------------------------------------
    # Messaging
    # ------------------------------------------------------------------

    def broadcast(self, payload: object, sender_id: Optional[str] = None) -> int:
        """Broadcast a message to all agents on the network topic.

        Returns:
            Number of agents that received the message.
        """
        msg = Message(topic=self.network_id, payload=payload, sender_id=sender_id)
        count = self.bus.publish(msg)
        logger.info(
            "Network '%s' broadcast to %d agent(s).", self.network_id, count
        )
        return count

    def send(
        self,
        topic: str,
        payload: object,
        sender_id: Optional[str] = None,
    ) -> int:
        """Publish a message on an arbitrary *topic* within this network.

        Returns:
            Number of agents that received the message.
        """
        msg = Message(topic=topic, payload=payload, sender_id=sender_id)
        return self.bus.publish(msg)

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    def agents(self) -> List["Agent"]:
        """Return a list of all agents currently in this network."""
        return list(self._agents.values())

    def get_agent(self, agent_id: str) -> Optional["Agent"]:
        """Return the agent with *agent_id*, or ``None`` if not found."""
        return self._agents.get(agent_id)

    def status(self) -> dict:
        """Return a status snapshot of this network."""
        return {
            "network_id": self.network_id,
            "agent_count": len(self._agents),
            "agents": [a.status() for a in self._agents.values()],
            "topics": self.bus.topics(),
        }

    def __repr__(self) -> str:  # pragma: no cover
        return f"Network(id={self.network_id!r}, agents={len(self._agents)})"
