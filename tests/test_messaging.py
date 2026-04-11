"""Tests for swarm.messaging."""

import pytest
from swarm.agent import Agent
from swarm.messaging import Message, MessageBus


def test_message_has_unique_id():
    m1 = Message("t", "p1")
    m2 = Message("t", "p2")
    assert m1.message_id != m2.message_id


def test_message_custom_id():
    msg = Message("t", "p", message_id="my-id")
    assert msg.message_id == "my-id"


def test_message_to_dict_keys():
    msg = Message("greet", {"text": "hi"}, sender_id="agent-1")
    d = msg.to_dict()
    assert d["topic"] == "greet"
    assert d["payload"] == {"text": "hi"}
    assert d["sender_id"] == "agent-1"
    assert "timestamp" in d


def test_message_bus_subscribe_and_publish():
    bus = MessageBus()
    agent = Agent("Sub")
    received = []
    agent.register_handler("news", lambda m: received.append(m))

    bus.subscribe("news", agent)
    bus.publish(Message("news", "headline"))
    assert len(received) == 1


def test_message_bus_unsubscribe():
    bus = MessageBus()
    agent = Agent("Sub")
    received = []
    agent.register_handler("news", lambda m: received.append(m))

    bus.subscribe("news", agent)
    bus.unsubscribe("news", agent)
    bus.publish(Message("news", "ignored"))
    assert len(received) == 0


def test_message_bus_publish_returns_count():
    bus = MessageBus()
    a1, a2 = Agent("A1"), Agent("A2")
    bus.subscribe("t", a1)
    bus.subscribe("t", a2)
    count = bus.publish(Message("t", "x"))
    assert count == 2


def test_message_bus_publish_no_subscribers_returns_zero():
    bus = MessageBus()
    count = bus.publish(Message("empty", "x"))
    assert count == 0


def test_message_bus_topics():
    bus = MessageBus()
    a = Agent("A")
    bus.subscribe("alpha", a)
    bus.subscribe("beta", a)
    assert set(bus.topics()) == {"alpha", "beta"}


def test_message_bus_history():
    bus = MessageBus()
    a = Agent("H")
    bus.subscribe("h", a)
    bus.publish(Message("h", 1))
    bus.publish(Message("h", 2))
    bus.publish(Message("other", 3))
    assert len(bus.history()) == 3
    assert len(bus.history(topic="h")) == 2


def test_message_bus_no_duplicate_subscribe():
    bus = MessageBus()
    a = Agent("D")
    bus.subscribe("t", a)
    bus.subscribe("t", a)
    # Only one copy – publish should deliver once
    received = []
    a.register_handler("t", lambda m: received.append(m))
    bus.publish(Message("t", "x"))
    assert len(received) == 1
