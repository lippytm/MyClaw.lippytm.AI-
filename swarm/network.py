"""
AI Swarm Network module.

Manages the topology of the swarm: which agents are connected to which,
how messages are routed across multi-hop paths, and overall network health
metrics.
"""

from __future__ import annotations

import threading
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


class ConnectionType(Enum):
    """Nature of the link between two network nodes."""

    DIRECT = "direct"        # Point-to-point physical/logical link
    RELAY = "relay"          # Message is forwarded via an intermediate node
    VIRTUAL = "virtual"      # Software-defined / overlay link


@dataclass
class NetworkLink:
    """Directed link between two agents in the swarm network.

    Attributes:
        source_id: Originating agent ID.
        target_id: Destination agent ID.
        connection_type: Nature of the connection.
        latency_ms: Estimated round-trip latency in milliseconds.
        bandwidth_mbps: Available bandwidth in Mbps.
        is_active: Whether the link is currently operational.
        metadata: Arbitrary link properties.
    """

    source_id: str
    target_id: str
    connection_type: ConnectionType = ConnectionType.DIRECT
    latency_ms: float = 0.0
    bandwidth_mbps: float = 0.0
    is_active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialise the link to a plain dictionary."""
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "connection_type": self.connection_type.value,
            "latency_ms": self.latency_ms,
            "bandwidth_mbps": self.bandwidth_mbps,
            "is_active": self.is_active,
            "metadata": dict(self.metadata),
        }


class NetworkTopology:
    """Manages and queries the swarm's network graph.

    The graph is *directed* (A→B is independent of B→A).  Helper methods
    treat the graph as undirected when computing undirected neighbours or
    shortest paths.

    All public methods are thread-safe.
    """

    def __init__(self) -> None:
        # adjacency: source_id → {target_id → NetworkLink}
        self._links: Dict[str, Dict[str, NetworkLink]] = {}
        self._nodes: Set[str] = set()
        self._lock = threading.RLock()

    # ------------------------------------------------------------------
    # Node management
    # ------------------------------------------------------------------

    def add_node(self, agent_id: str) -> None:
        """Register *agent_id* as a node in the topology."""
        with self._lock:
            self._nodes.add(agent_id)
            self._links.setdefault(agent_id, {})

    def remove_node(self, agent_id: str) -> None:
        """Remove *agent_id* and all of its links from the topology."""
        with self._lock:
            self._nodes.discard(agent_id)
            self._links.pop(agent_id, None)
            # Remove incoming links
            for neighbours in self._links.values():
                neighbours.pop(agent_id, None)

    def has_node(self, agent_id: str) -> bool:
        """Return ``True`` if *agent_id* is a registered node."""
        with self._lock:
            return agent_id in self._nodes

    def list_nodes(self) -> List[str]:
        """Return a snapshot of all node IDs."""
        with self._lock:
            return list(self._nodes)

    # ------------------------------------------------------------------
    # Link management
    # ------------------------------------------------------------------

    def add_link(self, link: NetworkLink) -> None:
        """Add (or replace) a directed link in the topology.

        Automatically registers both endpoints as nodes if not already
        present.
        """
        with self._lock:
            self._nodes.add(link.source_id)
            self._nodes.add(link.target_id)
            self._links.setdefault(link.source_id, {})[link.target_id] = link

    def remove_link(self, source_id: str, target_id: str) -> bool:
        """Remove the directed link *source_id*→*target_id*.

        Returns:
            ``True`` if the link existed and was removed.
        """
        with self._lock:
            if source_id in self._links:
                existed = target_id in self._links[source_id]
                self._links[source_id].pop(target_id, None)
                return existed
            return False

    def get_link(
        self, source_id: str, target_id: str
    ) -> Optional[NetworkLink]:
        """Return the directed link *source_id*→*target_id*, or ``None``."""
        with self._lock:
            return self._links.get(source_id, {}).get(target_id)

    def set_link_active(
        self, source_id: str, target_id: str, active: bool
    ) -> bool:
        """Enable or disable a link without removing it.

        Returns:
            ``True`` if the link was found and updated.
        """
        with self._lock:
            link = self._links.get(source_id, {}).get(target_id)
            if link is None:
                return False
            link.is_active = active
            return True

    def list_links(self) -> List[NetworkLink]:
        """Return a snapshot of all links (active and inactive)."""
        with self._lock:
            return [
                link
                for neighbours in self._links.values()
                for link in neighbours.values()
            ]

    # ------------------------------------------------------------------
    # Neighbours
    # ------------------------------------------------------------------

    def get_direct_neighbours(self, agent_id: str) -> List[str]:
        """Return IDs of all nodes reachable via a single active hop."""
        with self._lock:
            return [
                target
                for target, link in self._links.get(agent_id, {}).items()
                if link.is_active
            ]

    # ------------------------------------------------------------------
    # Path finding (BFS shortest path)
    # ------------------------------------------------------------------

    def find_path(
        self, source_id: str, target_id: str
    ) -> Optional[List[str]]:
        """Return the shortest hop path from *source_id* to *target_id*.

        Only follows active links.  Returns ``None`` when no path exists.
        The returned list includes both endpoints, e.g. ``["A", "B", "C"]``.
        """
        with self._lock:
            if source_id not in self._nodes or target_id not in self._nodes:
                return None
            if source_id == target_id:
                return [source_id]

            visited: Set[str] = {source_id}
            queue: deque[List[str]] = deque([[source_id]])

            while queue:
                path = queue.popleft()
                current = path[-1]
                for neighbour, link in self._links.get(current, {}).items():
                    if not link.is_active:
                        continue
                    if neighbour == target_id:
                        return path + [neighbour]
                    if neighbour not in visited:
                        visited.add(neighbour)
                        queue.append(path + [neighbour])
        return None

    # ------------------------------------------------------------------
    # Network metrics
    # ------------------------------------------------------------------

    def node_count(self) -> int:
        """Return the total number of nodes."""
        with self._lock:
            return len(self._nodes)

    def link_count(self, active_only: bool = False) -> int:
        """Return the number of links, optionally restricted to active ones."""
        with self._lock:
            total = 0
            for neighbours in self._links.values():
                for link in neighbours.values():
                    if active_only and not link.is_active:
                        continue
                    total += 1
            return total

    def get_network_summary(self) -> Dict[str, Any]:
        """Return a high-level summary of the network topology."""
        with self._lock:
            total = self.link_count()
            active = self.link_count(active_only=True)
            return {
                "node_count": self.node_count(),
                "link_count": total,
                "active_link_count": active,
                "inactive_link_count": total - active,
                "nodes": list(self._nodes),
            }

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_dict(self) -> Dict[str, Any]:
        """Serialise the entire topology."""
        with self._lock:
            return {
                "nodes": list(self._nodes),
                "links": [link.to_dict() for link in self.list_links()],
            }
