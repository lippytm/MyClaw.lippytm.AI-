"""Tests for swarm.agent."""

import pytest
from swarm.agent import Agent


def test_agent_default_id_is_unique():
    a1 = Agent("Alpha")
    a2 = Agent("Beta")
    assert a1.agent_id != a2.agent_id


def test_agent_custom_id():
    agent = Agent("Custom", agent_id="fixed-id-123")
    assert agent.agent_id == "fixed-id-123"


def test_agent_capabilities_default_empty():
    agent = Agent("NoSkills")
    assert agent.capabilities == []


def test_agent_capabilities_stored():
    agent = Agent("Skilled", capabilities=["nlp", "vision"])
    assert "nlp" in agent.capabilities
    assert "vision" in agent.capabilities


def test_agent_receive_dispatches_handler():
    received = []
    agent = Agent("Listener")
    agent.register_handler("ping", lambda msg: received.append(msg))

    agent.receive({"topic": "ping", "payload": "hello"})
    assert len(received) == 1
    assert received[0]["payload"] == "hello"


def test_agent_receive_unhandled_topic_no_error():
    agent = Agent("Silent")
    # Should not raise even without a registered handler
    agent.receive({"topic": "unknown", "payload": None})


def test_agent_inbox_grows():
    agent = Agent("Collector")
    agent.receive({"topic": "a", "payload": 1})
    agent.receive({"topic": "b", "payload": 2})
    assert agent.status()["inbox_size"] == 2


def test_agent_status_shape():
    agent = Agent("Reporter", capabilities=["c1"], agent_id="test-id")
    s = agent.status()
    assert s["agent_id"] == "test-id"
    assert s["name"] == "Reporter"
    assert s["capabilities"] == ["c1"]
    assert "inbox_size" in s
