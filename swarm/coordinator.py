"""
swarm/coordinator.py – Swarm Coordinator for the MyClaw System.

The Coordinator manages multiple Networks and Agents, provides global
routing, and orchestrates task distribution across the swarm.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, TYPE_CHECKING

from swarm.network import Network

if TYPE_CHECKING:
    from swarm.agent import Agent

logger = logging.getLogger(__name__)


class Coordinator:
    """Central coordinator that manages a collection of Networks and Agents.

    Responsibilities:
      - Maintain a registry of networks and agents.
      - Route messages between networks.
      - Distribute tasks to capable agents.
      - Report overall swarm health.
    """

    def __init__(self, name: str = "MainCoordinator") -> None:
        self.name: str = name
        self._networks: Dict[str, Network] = {}
        self._agents: Dict[str, "Agent"] = {}
        logger.info("Coordinator '%s' initialised.", self.name)

    # ------------------------------------------------------------------
    # Network management
    # ------------------------------------------------------------------

    def create_network(self, network_id: str) -> Network:
        """Create and register a new :class:`~swarm.network.Network`."""
        if network_id in self._networks:
            raise ValueError(f"Network '{network_id}' already exists.")
        network = Network(network_id)
        self._networks[network_id] = network
        logger.info("Coordinator '%s' created network '%s'.", self.name, network_id)
        return network

    def get_network(self, network_id: str) -> Optional[Network]:
        """Return the network with *network_id*, or ``None``."""
        return self._networks.get(network_id)

    def remove_network(self, network_id: str) -> None:
        """Remove a network from the coordinator registry."""
        self._networks.pop(network_id, None)
        logger.info(
            "Coordinator '%s' removed network '%s'.", self.name, network_id
        )

    # ------------------------------------------------------------------
    # Agent management
    # ------------------------------------------------------------------

    def register_agent(self, agent: "Agent") -> None:
        """Register an agent with the coordinator (does not add to any network)."""
        self._agents[agent.agent_id] = agent
        logger.debug(
            "Coordinator '%s' registered agent '%s'.", self.name, agent.name
        )

    def assign_agent(self, agent: "Agent", network_id: str) -> None:
        """Register *agent* and add it to the specified network."""
        self.register_agent(agent)
        network = self._networks.get(network_id)
        if network is None:
            raise ValueError(f"Network '{network_id}' does not exist.")
        network.add_agent(agent)

    # ------------------------------------------------------------------
    # Task distribution
    # ------------------------------------------------------------------

    def dispatch_task(
        self,
        task: dict,
        capability: Optional[str] = None,
        network_id: Optional[str] = None,
    ) -> List[str]:
        """Dispatch a task to agents that match an optional *capability* filter.

        If *network_id* is provided, only agents in that network are considered.
        If *capability* is provided, only agents advertising that capability
        receive the task.

        Returns:
            List of agent ids that received the task.
        """
        if network_id:
            network = self._networks.get(network_id)
            candidates = network.agents() if network else []
        else:
            candidates = list(self._agents.values())

        if capability:
            candidates = [a for a in candidates if capability in a.capabilities]

        task_message = {"topic": "task", "payload": task}
        dispatched: List[str] = []
        for agent in candidates:
            agent.receive(task_message)
            dispatched.append(agent.agent_id)

        logger.info(
            "Coordinator '%s' dispatched task to %d agent(s).",
            self.name,
            len(dispatched),
        )
        return dispatched

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    def status(self) -> dict:
        """Return an overall status snapshot of the swarm."""
        return {
            "coordinator": self.name,
            "network_count": len(self._networks),
            "agent_count": len(self._agents),
            "networks": {nid: n.status() for nid, n in self._networks.items()},
        }

    def __repr__(self) -> str:  # pragma: no cover
        return (
            f"Coordinator(name={self.name!r}, "
            f"networks={len(self._networks)}, agents={len(self._agents)})"
        )
