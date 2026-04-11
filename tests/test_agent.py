"""Tests for swarm.agent module."""

import pytest

from swarm.agent import Agent, AgentStatus
from swarm.messaging import Message, MessageType


class TestAgentCreation:
    def test_default_id_is_uuid(self):
        agent = Agent("Alpha")
        assert len(agent.agent_id) == 36  # UUID4 canonical form
        assert agent.agent_id.count("-") == 4

    def test_custom_id(self):
        agent = Agent("Beta", agent_id="custom-id-1")
        assert agent.agent_id == "custom-id-1"

    def test_initial_status_is_initializing(self):
        agent = Agent("Gamma")
        assert agent.status == AgentStatus.INITIALIZING

    def test_capabilities_default_empty(self):
        agent = Agent("Delta")
        assert agent.capabilities == []

    def test_capabilities_set_at_construction(self):
        agent = Agent("Epsilon", capabilities=["nlp", "vision"])
        assert agent.capabilities == ["nlp", "vision"]

    def test_metadata_default_empty(self):
        agent = Agent("Zeta")
        assert agent.metadata == {}


class TestAgentStatus:
    def test_set_online(self):
        agent = Agent("Alpha")
        agent.set_online()
        assert agent.status == AgentStatus.ONLINE
        assert agent.is_available is True

    def test_set_offline(self):
        agent = Agent("Alpha")
        agent.set_online()
        agent.set_offline()
        assert agent.status == AgentStatus.OFFLINE
        assert agent.is_available is False

    def test_set_busy(self):
        agent = Agent("Alpha")
        agent.set_online()
        agent.set_busy()
        assert agent.status == AgentStatus.BUSY
        assert agent.is_available is False

    def test_set_error(self):
        agent = Agent("Alpha")
        agent.set_error()
        assert agent.status == AgentStatus.ERROR


class TestAgentCapabilities:
    def test_has_capability_true(self):
        agent = Agent("Alpha", capabilities=["nlp"])
        assert agent.has_capability("nlp") is True

    def test_has_capability_false(self):
        agent = Agent("Alpha", capabilities=["nlp"])
        assert agent.has_capability("vision") is False

    def test_add_capability(self):
        agent = Agent("Alpha")
        agent.add_capability("nlp")
        assert "nlp" in agent.capabilities

    def test_add_capability_no_duplicates(self):
        agent = Agent("Alpha", capabilities=["nlp"])
        agent.add_capability("nlp")
        assert agent.capabilities.count("nlp") == 1

    def test_remove_capability(self):
        agent = Agent("Alpha", capabilities=["nlp", "vision"])
        agent.remove_capability("nlp")
        assert "nlp" not in agent.capabilities
        assert "vision" in agent.capabilities

    def test_remove_nonexistent_capability_no_error(self):
        agent = Agent("Alpha")
        agent.remove_capability("audio")  # should not raise


class TestAgentMessaging:
    def _make_message(self, sender="sys", receiver="agent-1"):
        return Message(
            sender_id=sender,
            receiver_id=receiver,
            message_type=MessageType.DATA,
            payload="hello",
        )

    def test_deliver_adds_to_inbox(self):
        agent = Agent("Alpha", agent_id="agent-1")
        msg = self._make_message(receiver="agent-1")
        agent.deliver(msg)
        assert agent.inbox_size() == 1

    def test_receive_pops_message(self):
        agent = Agent("Alpha", agent_id="agent-1")
        msg = self._make_message(receiver="agent-1")
        agent.deliver(msg)
        received = agent.receive()
        assert received is msg
        assert agent.inbox_size() == 0

    def test_receive_empty_inbox_returns_none(self):
        agent = Agent("Alpha")
        assert agent.receive() is None

    def test_message_handler_invoked(self):
        results = []
        agent = Agent("Alpha", agent_id="agent-1")
        agent.set_message_handler(lambda m: results.append(m))
        msg = self._make_message(receiver="agent-1")
        agent.deliver(msg)
        assert results == [msg]

    def test_multiple_messages_fifo_order(self):
        agent = Agent("Alpha", agent_id="agent-1")
        msgs = [self._make_message() for _ in range(3)]
        for m in msgs:
            agent.deliver(m)
        for m in msgs:
            assert agent.receive() is m


class TestAgentSerialisation:
    def test_to_dict_keys(self):
        agent = Agent("Alpha", capabilities=["nlp"], agent_id="id-1")
        d = agent.to_dict()
        assert set(d.keys()) == {
            "agent_id", "name", "capabilities", "status", "metadata"
        }

    def test_to_dict_values(self):
        agent = Agent("Alpha", capabilities=["nlp"], agent_id="id-1")
        agent.set_online()
        d = agent.to_dict()
        assert d["agent_id"] == "id-1"
        assert d["name"] == "Alpha"
        assert d["capabilities"] == ["nlp"]
        assert d["status"] == "online"
