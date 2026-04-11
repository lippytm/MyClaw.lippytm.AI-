"""Tests for swarm.network."""

import pytest
from swarm.agent import Agent
from swarm.network import Network


def test_network_add_agent():
    net = Network("test-net")
    a = Agent("Alpha")
    net.add_agent(a)
    assert a in net.agents()


def test_network_remove_agent():
    net = Network("test-net")
    a = Agent("Beta")
    net.add_agent(a)
    net.remove_agent(a)
    assert a not in net.agents()


def test_network_broadcast_reaches_all_agents():
    net = Network("broadcast-net")
    received = {1: [], 2: []}
    a1 = Agent("A1")
    a2 = Agent("A2")
    a1.register_handler("broadcast-net", lambda m: received[1].append(m))
    a2.register_handler("broadcast-net", lambda m: received[2].append(m))
    net.add_agent(a1)
    net.add_agent(a2)
    count = net.broadcast("hello")
    assert count == 2
    assert len(received[1]) == 1
    assert len(received[2]) == 1


def test_network_send_to_custom_topic():
    net = Network("mynet")
    received = []
    a = Agent("Listener")
    a.register_handler("custom", lambda m: received.append(m))
    net.add_agent(a)
    net.bus.subscribe("custom", a)
    net.send("custom", {"data": 42})
    assert len(received) == 1


def test_network_get_agent():
    net = Network("lookup-net")
    a = Agent("FindMe", agent_id="known-id")
    net.add_agent(a)
    assert net.get_agent("known-id") is a
    assert net.get_agent("missing") is None


def test_network_status():
    net = Network("status-net")
    net.add_agent(Agent("S1"))
    net.add_agent(Agent("S2"))
    s = net.status()
    assert s["network_id"] == "status-net"
    assert s["agent_count"] == 2
    assert len(s["agents"]) == 2
