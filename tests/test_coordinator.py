"""Tests for swarm.coordinator."""

import pytest
from swarm.agent import Agent
from swarm.coordinator import Coordinator


def test_coordinator_create_network():
    c = Coordinator()
    net = c.create_network("net1")
    assert c.get_network("net1") is net


def test_coordinator_duplicate_network_raises():
    c = Coordinator()
    c.create_network("dup")
    with pytest.raises(ValueError, match="already exists"):
        c.create_network("dup")


def test_coordinator_remove_network():
    c = Coordinator()
    c.create_network("to-remove")
    c.remove_network("to-remove")
    assert c.get_network("to-remove") is None


def test_coordinator_assign_agent():
    c = Coordinator()
    c.create_network("n")
    a = Agent("Worker")
    c.assign_agent(a, "n")
    assert a in c.get_network("n").agents()


def test_coordinator_assign_agent_missing_network():
    c = Coordinator()
    with pytest.raises(ValueError, match="does not exist"):
        c.assign_agent(Agent("X"), "ghost")


def test_coordinator_dispatch_task_all_agents():
    c = Coordinator()
    c.create_network("workers")
    received = {1: [], 2: []}
    a1, a2 = Agent("W1"), Agent("W2")
    a1.register_handler("task", lambda m: received[1].append(m))
    a2.register_handler("task", lambda m: received[2].append(m))
    c.assign_agent(a1, "workers")
    c.assign_agent(a2, "workers")
    dispatched = c.dispatch_task({"job": "analyze"})
    assert len(dispatched) == 2


def test_coordinator_dispatch_task_capability_filter():
    c = Coordinator()
    c.create_network("mixed")
    nlp_agent = Agent("NLP", capabilities=["nlp"])
    vision_agent = Agent("Vision", capabilities=["vision"])
    c.assign_agent(nlp_agent, "mixed")
    c.assign_agent(vision_agent, "mixed")
    dispatched = c.dispatch_task({"job": "translate"}, capability="nlp")
    assert nlp_agent.agent_id in dispatched
    assert vision_agent.agent_id not in dispatched


def test_coordinator_dispatch_task_network_filter():
    c = Coordinator()
    c.create_network("netA")
    c.create_network("netB")
    a_a = Agent("InA")
    a_b = Agent("InB")
    c.assign_agent(a_a, "netA")
    c.assign_agent(a_b, "netB")
    dispatched = c.dispatch_task({"job": "x"}, network_id="netA")
    assert a_a.agent_id in dispatched
    assert a_b.agent_id not in dispatched


def test_coordinator_status():
    c = Coordinator(name="TestCoord")
    c.create_network("sn")
    c.assign_agent(Agent("SA"), "sn")
    s = c.status()
    assert s["coordinator"] == "TestCoord"
    assert s["network_count"] == 1
    assert s["agent_count"] == 1
