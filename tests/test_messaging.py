"""Tests for swarm.messaging module."""

import pytest

from swarm.agent import Agent
from swarm.messaging import Message, MessageBus, MessageType


def make_agent(name: str, agent_id: str | None = None) -> Agent:
    a = Agent(name, agent_id=agent_id or name.lower())
    a.set_online()
    return a


class TestMessage:
    def test_default_id_and_timestamp(self):
        msg = Message(
            sender_id="a",
            receiver_id="b",
            message_type=MessageType.DATA,
        )
        assert msg.message_id  # not empty
        assert msg.timestamp is not None

    def test_to_dict_has_all_keys(self):
        msg = Message(
            sender_id="a",
            receiver_id="b",
            message_type=MessageType.COMMAND,
            payload={"cmd": "run"},
        )
        d = msg.to_dict()
        assert "message_id" in d
        assert d["sender_id"] == "a"
        assert d["receiver_id"] == "b"
        assert d["message_type"] == "command"
        assert d["payload"] == {"cmd": "run"}


class TestMessageBusUnicast:
    def setup_method(self):
        self.bus = MessageBus()
        self.agent_a = make_agent("Alpha", "alpha")
        self.agent_b = make_agent("Beta", "beta")
        self.bus.register_agent(self.agent_a)
        self.bus.register_agent(self.agent_b)

    def test_send_delivers_to_receiver(self):
        msg = Message("alpha", "beta", MessageType.DATA, "hi")
        assert self.bus.send(msg) is True
        assert self.agent_b.inbox_size() == 1
        assert self.agent_a.inbox_size() == 0

    def test_send_returns_false_unknown_receiver(self):
        msg = Message("alpha", "unknown", MessageType.DATA)
        assert self.bus.send(msg) is False

    def test_send_logs_message(self):
        msg = Message("alpha", "beta", MessageType.DATA)
        self.bus.send(msg)
        assert len(self.bus.get_message_log()) == 1

    def test_unregister_prevents_delivery(self):
        self.bus.unregister_agent("beta")
        msg = Message("alpha", "beta", MessageType.DATA)
        assert self.bus.send(msg) is False


class TestMessageBusBroadcast:
    def setup_method(self):
        self.bus = MessageBus()
        self.agents = [make_agent(f"Agent-{i}", f"agent-{i}") for i in range(4)]
        for a in self.agents:
            self.bus.register_agent(a)

    def test_broadcast_reaches_all_except_sender(self):
        msg = Message("agent-0", None, MessageType.BROADCAST, "ping")
        count = self.bus.broadcast(msg)
        assert count == 3
        assert self.agents[0].inbox_size() == 0
        for a in self.agents[1:]:
            assert a.inbox_size() == 1

    def test_broadcast_logs_message(self):
        msg = Message("agent-0", None, MessageType.BROADCAST)
        self.bus.broadcast(msg)
        assert len(self.bus.get_message_log()) == 1


class TestMessageBusPubSub:
    def setup_method(self):
        self.bus = MessageBus()
        self.agent_a = make_agent("Alpha", "alpha")
        self.agent_b = make_agent("Beta", "beta")
        self.agent_c = make_agent("Gamma", "gamma")
        for a in [self.agent_a, self.agent_b, self.agent_c]:
            self.bus.register_agent(a)

    def test_publish_reaches_subscribers(self):
        self.bus.subscribe("beta", "news")
        self.bus.subscribe("gamma", "news")
        msg = Message("alpha", None, MessageType.DATA, topic="news")
        count = self.bus.publish(msg)
        assert count == 2
        assert self.agent_b.inbox_size() == 1
        assert self.agent_c.inbox_size() == 1
        assert self.agent_a.inbox_size() == 0

    def test_publish_without_topic_raises(self):
        msg = Message("alpha", None, MessageType.DATA)
        with pytest.raises(ValueError):
            self.bus.publish(msg)

    def test_unsubscribe_stops_delivery(self):
        self.bus.subscribe("beta", "events")
        self.bus.unsubscribe("beta", "events")
        msg = Message("alpha", None, MessageType.DATA, topic="events")
        count = self.bus.publish(msg)
        assert count == 0
        assert self.agent_b.inbox_size() == 0

    def test_subscribe_handler_invoked(self):
        received = []
        self.bus.subscribe_handler("alerts", lambda m: received.append(m))
        msg = Message("alpha", None, MessageType.DATA, topic="alerts")
        self.bus.publish(msg)
        assert len(received) == 1
        assert received[0] is msg

    def test_get_topic_subscribers(self):
        self.bus.subscribe("alpha", "feed")
        self.bus.subscribe("beta", "feed")
        subs = self.bus.get_topic_subscribers("feed")
        assert set(subs) == {"alpha", "beta"}


class TestMessageBusLog:
    def test_clear_log(self):
        bus = MessageBus()
        agent = make_agent("A", "a")
        bus.register_agent(agent)
        msg = Message("sys", "a", MessageType.DATA)
        bus.send(msg)
        assert len(bus.get_message_log()) == 1
        bus.clear_log()
        assert len(bus.get_message_log()) == 0

    def test_list_agents(self):
        bus = MessageBus()
        agent = make_agent("A", "a")
        bus.register_agent(agent)
        assert agent in bus.list_agents()
        bus.unregister_agent("a")
        assert agent not in bus.list_agents()
