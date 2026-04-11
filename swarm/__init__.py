"""
swarm – AI Swarm Communications and Networking Management System.

Public API
----------

.. code-block:: python

    from swarm import SwarmCoordinator, Agent, AgentStatus
    from swarm import Message, MessageBus, MessageType
    from swarm import NetworkTopology, NetworkLink, ConnectionType

"""

from .agent import Agent, AgentStatus
from .coordinator import SwarmCoordinator
from .messaging import Message, MessageBus, MessageType
from .network import ConnectionType, NetworkLink, NetworkTopology

__all__ = [
    "Agent",
    "AgentStatus",
    "ConnectionType",
    "Message",
    "MessageBus",
    "MessageType",
    "NetworkLink",
    "NetworkTopology",
    "SwarmCoordinator",
]
