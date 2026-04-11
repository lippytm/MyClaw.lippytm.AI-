"""
AI Swarm Coordinator module.

The :class:`SwarmCoordinator` is the central orchestrator of the AI swarm.
It wires together the :class:`~swarm.messaging.MessageBus`,
:class:`~swarm.network.NetworkTopology`, and the individual
:class:`~swarm.agent.Agent` instances, and provides high-level operations
such as agent registration, task dispatch, capability-based routing,
heartbeat monitoring, and status reporting.
"""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from .agent import Agent, AgentStatus
from .messaging import Message, MessageBus, MessageType
from .network import ConnectionType, NetworkLink, NetworkTopology


class SwarmCoordinator:
    """Central coordinator for the AI swarm.

    Responsibilities
    ----------------
    * Register and deregister :class:`~swarm.agent.Agent` instances.
    * Maintain the :class:`~swarm.network.NetworkTopology` in sync with
      agent membership.
    * Route tasks to the best available agent based on capabilities.
    * Broadcast status and heartbeat messages.
    * Expose swarm-wide health metrics.

    Example::

        coordinator = SwarmCoordinator()

        agent_a = Agent("Worker-A", capabilities=["nlp"])
        agent_b = Agent("Worker-B", capabilities=["vision"])

        coordinator.register_agent(agent_a)
        coordinator.register_agent(agent_b)

        coordinator.dispatch_task(
            task_payload={"query": "Hello world"},
            required_capability="nlp",
            sender_id="system",
        )
    """

    SYSTEM_ID = "system"

    def __init__(self) -> None:
        self._bus = MessageBus()
        self._topology = NetworkTopology()
        self._agents: Dict[str, Agent] = {}
        self._lock = threading.RLock()

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def bus(self) -> MessageBus:
        """The underlying :class:`~swarm.messaging.MessageBus`."""
        return self._bus

    @property
    def topology(self) -> NetworkTopology:
        """The underlying :class:`~swarm.network.NetworkTopology`."""
        return self._topology

    # ------------------------------------------------------------------
    # Agent lifecycle
    # ------------------------------------------------------------------

    def register_agent(
        self,
        agent: Agent,
        connect_to: Optional[List[str]] = None,
        link_type: ConnectionType = ConnectionType.DIRECT,
    ) -> None:
        """Register *agent* with the swarm.

        The agent is added to the message bus and the network topology.
        If *connect_to* is supplied, bidirectional links are created
        between *agent* and each listed agent ID.

        Args:
            agent: The agent to add.
            connect_to: Optional list of existing agent IDs to link to.
            link_type: :class:`~swarm.network.ConnectionType` for the
                auto-created links.
        """
        with self._lock:
            self._agents[agent.agent_id] = agent
            self._bus.register_agent(agent)
            self._topology.add_node(agent.agent_id)
            agent.set_online()

            if connect_to:
                for peer_id in connect_to:
                    if peer_id not in self._agents:
                        continue
                    self._topology.add_link(
                        NetworkLink(
                            source_id=agent.agent_id,
                            target_id=peer_id,
                            connection_type=link_type,
                        )
                    )
                    self._topology.add_link(
                        NetworkLink(
                            source_id=peer_id,
                            target_id=agent.agent_id,
                            connection_type=link_type,
                        )
                    )

    def deregister_agent(self, agent_id: str) -> Optional[Agent]:
        """Remove an agent from the swarm.

        Returns the removed :class:`~swarm.agent.Agent`, or ``None`` if
        the ID was not found.
        """
        with self._lock:
            agent = self._agents.pop(agent_id, None)
            if agent is not None:
                agent.set_offline()
                self._bus.unregister_agent(agent_id)
                self._topology.remove_node(agent_id)
            return agent

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        """Return the agent with *agent_id*, or ``None``."""
        with self._lock:
            return self._agents.get(agent_id)

    def list_agents(self) -> List[Agent]:
        """Return a snapshot of all registered agents."""
        with self._lock:
            return list(self._agents.values())

    def agents_by_capability(self, capability: str) -> List[Agent]:
        """Return all online agents that advertise *capability*."""
        with self._lock:
            return [
                a
                for a in self._agents.values()
                if a.has_capability(capability) and a.is_available
            ]

    # ------------------------------------------------------------------
    # Messaging helpers
    # ------------------------------------------------------------------

    def send_message(
        self,
        sender_id: str,
        receiver_id: str,
        message_type: MessageType,
        payload: Any = None,
        **kwargs: Any,
    ) -> bool:
        """Send a unicast message and return whether delivery succeeded."""
        message = Message(
            sender_id=sender_id,
            receiver_id=receiver_id,
            message_type=message_type,
            payload=payload,
            **kwargs,
        )
        return self._bus.send(message)

    def broadcast_message(
        self,
        message_type: MessageType,
        payload: Any = None,
        sender_id: Optional[str] = None,
        **kwargs: Any,
    ) -> int:
        """Broadcast a message to all agents (excluding the sender).

        Returns the number of agents that received the message.
        """
        message = Message(
            sender_id=sender_id or self.SYSTEM_ID,
            receiver_id=None,
            message_type=message_type,
            payload=payload,
            **kwargs,
        )
        return self._bus.broadcast(message)

    def publish_to_topic(
        self,
        topic: str,
        payload: Any = None,
        sender_id: Optional[str] = None,
        message_type: MessageType = MessageType.DATA,
        **kwargs: Any,
    ) -> int:
        """Publish a message to *topic*.

        Returns the total number of deliveries (agents + handlers).
        """
        message = Message(
            sender_id=sender_id or self.SYSTEM_ID,
            receiver_id=None,
            message_type=message_type,
            payload=payload,
            topic=topic,
            **kwargs,
        )
        return self._bus.publish(message)

    # ------------------------------------------------------------------
    # Task dispatch
    # ------------------------------------------------------------------

    def dispatch_task(
        self,
        task_payload: Any,
        required_capability: Optional[str] = None,
        sender_id: Optional[str] = None,
        target_agent_id: Optional[str] = None,
    ) -> Optional[str]:
        """Dispatch a task to the most suitable available agent.

        Selection priority:
        1. *target_agent_id* if explicitly specified.
        2. The available agent with the fewest inbox messages that has
           *required_capability* (if given).
        3. Any available agent (if no capability requirement).

        Returns:
            The ``agent_id`` of the agent that received the task, or
            ``None`` if no suitable agent was found.
        """
        agent: Optional[Agent] = None

        if target_agent_id:
            agent = self._agents.get(target_agent_id)
        elif required_capability:
            candidates = self.agents_by_capability(required_capability)
            if candidates:
                agent = min(candidates, key=lambda a: a.inbox_size())
        else:
            with self._lock:
                online = [
                    a
                    for a in self._agents.values()
                    if a.is_available
                ]
            if online:
                agent = min(online, key=lambda a: a.inbox_size())

        if agent is None:
            return None

        message = Message(
            sender_id=sender_id or self.SYSTEM_ID,
            receiver_id=agent.agent_id,
            message_type=MessageType.TASK_REQUEST,
            payload=task_payload,
        )
        self._bus.send(message)
        return agent.agent_id

    # ------------------------------------------------------------------
    # Heartbeat
    # ------------------------------------------------------------------

    def send_heartbeat(self) -> int:
        """Broadcast a heartbeat to all registered agents.

        Returns the number of agents that received the heartbeat.
        """
        return self.broadcast_message(
            message_type=MessageType.HEARTBEAT,
            payload={"timestamp": datetime.now(timezone.utc).isoformat()},
        )

    # ------------------------------------------------------------------
    # Network helpers
    # ------------------------------------------------------------------

    def add_network_link(
        self,
        source_id: str,
        target_id: str,
        bidirectional: bool = True,
        connection_type: ConnectionType = ConnectionType.DIRECT,
        latency_ms: float = 0.0,
        bandwidth_mbps: float = 0.0,
    ) -> None:
        """Add a network link between two agents.

        Args:
            source_id: ID of the source agent.
            target_id: ID of the target agent.
            bidirectional: When ``True`` (default) the reverse link is
                also created.
            connection_type: Type of connection.
            latency_ms: Estimated latency in milliseconds.
            bandwidth_mbps: Available bandwidth in Mbps.
        """
        link_kwargs = dict(
            connection_type=connection_type,
            latency_ms=latency_ms,
            bandwidth_mbps=bandwidth_mbps,
        )
        self._topology.add_link(
            NetworkLink(source_id=source_id, target_id=target_id, **link_kwargs)
        )
        if bidirectional:
            self._topology.add_link(
                NetworkLink(source_id=target_id, target_id=source_id, **link_kwargs)
            )

    def find_route(
        self, source_id: str, target_id: str
    ) -> Optional[List[str]]:
        """Return the shortest active path from *source_id* to *target_id*."""
        return self._topology.find_path(source_id, target_id)

    # ------------------------------------------------------------------
    # Status & health
    # ------------------------------------------------------------------

    def get_swarm_status(self) -> Dict[str, Any]:
        """Return a comprehensive snapshot of swarm health."""
        with self._lock:
            agents_info = [a.to_dict() for a in self._agents.values()]
            status_counts: Dict[str, int] = {}
            for a in self._agents.values():
                status_counts[a.status.value] = (
                    status_counts.get(a.status.value, 0) + 1
                )

        return {
            "total_agents": len(agents_info),
            "status_breakdown": status_counts,
            "agents": agents_info,
            "network": self._topology.get_network_summary(),
            "message_log_size": len(self._bus.get_message_log()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def subscribe_agent_to_topic(self, agent_id: str, topic: str) -> None:
        """Subscribe an agent to a pub/sub topic."""
        self._bus.subscribe(agent_id, topic)

    def subscribe_handler_to_topic(
        self, topic: str, handler: Callable[[Message], None]
    ) -> None:
        """Register a system-level handler for a pub/sub topic."""
        self._bus.subscribe_handler(topic, handler)
