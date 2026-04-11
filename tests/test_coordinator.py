"""Tests for swarm.coordinator module."""

import pytest

from swarm import Agent, AgentStatus, MessageType, SwarmCoordinator
from swarm.network import ConnectionType


def _coordinator_with_agents(*names):
    """Create a coordinator pre-loaded with named agents."""
    coordinator = SwarmCoordinator()
    agents = {}
    for name in names:
        a = Agent(name, capabilities=[name.lower()], agent_id=name.lower())
        coordinator.register_agent(a)
        agents[name] = a
    return coordinator, agents


class TestAgentRegistration:
    def test_register_makes_agent_online(self):
        coordinator = SwarmCoordinator()
        agent = Agent("Alpha", agent_id="alpha")
        coordinator.register_agent(agent)
        assert agent.status == AgentStatus.ONLINE

    def test_register_adds_to_topology(self):
        coordinator = SwarmCoordinator()
        agent = Agent("Alpha", agent_id="alpha")
        coordinator.register_agent(agent)
        assert coordinator.topology.has_node("alpha")

    def test_register_with_connect_to_creates_links(self):
        coordinator = SwarmCoordinator()
        agent_a = Agent("Alpha", agent_id="alpha")
        agent_b = Agent("Beta", agent_id="beta")
        coordinator.register_agent(agent_a)
        coordinator.register_agent(agent_b, connect_to=["alpha"])
        assert coordinator.topology.get_link("beta", "alpha") is not None
        assert coordinator.topology.get_link("alpha", "beta") is not None

    def test_deregister_sets_offline(self):
        coordinator = SwarmCoordinator()
        agent = Agent("Alpha", agent_id="alpha")
        coordinator.register_agent(agent)
        coordinator.deregister_agent("alpha")
        assert agent.status == AgentStatus.OFFLINE

    def test_deregister_removes_from_topology(self):
        coordinator = SwarmCoordinator()
        agent = Agent("Alpha", agent_id="alpha")
        coordinator.register_agent(agent)
        coordinator.deregister_agent("alpha")
        assert not coordinator.topology.has_node("alpha")

    def test_deregister_unknown_returns_none(self):
        coordinator = SwarmCoordinator()
        assert coordinator.deregister_agent("ghost") is None

    def test_list_agents(self):
        coordinator, agents = _coordinator_with_agents("A", "B", "C")
        listed = coordinator.list_agents()
        assert len(listed) == 3

    def test_get_agent(self):
        coordinator, agents = _coordinator_with_agents("Alpha")
        assert coordinator.get_agent("alpha") is agents["Alpha"]

    def test_get_agent_unknown_returns_none(self):
        coordinator = SwarmCoordinator()
        assert coordinator.get_agent("ghost") is None


class TestAgentsByCapability:
    def test_returns_agents_with_capability(self):
        coordinator = SwarmCoordinator()
        nlp_agent = Agent("NLP", capabilities=["nlp"], agent_id="nlp")
        vision_agent = Agent("Vision", capabilities=["vision"], agent_id="vision")
        coordinator.register_agent(nlp_agent)
        coordinator.register_agent(vision_agent)
        result = coordinator.agents_by_capability("nlp")
        assert nlp_agent in result
        assert vision_agent not in result

    def test_excludes_offline_agents(self):
        coordinator = SwarmCoordinator()
        agent = Agent("NLP", capabilities=["nlp"], agent_id="nlp")
        coordinator.register_agent(agent)
        agent.set_offline()
        assert coordinator.agents_by_capability("nlp") == []


class TestTaskDispatch:
    def test_dispatch_to_capable_agent(self):
        coordinator, agents = _coordinator_with_agents("Alpha", "Beta")
        alpha = agents["Alpha"]
        # alpha has capability "alpha"
        target = coordinator.dispatch_task(
            {"job": "process"}, required_capability="alpha"
        )
        assert target == "alpha"
        assert alpha.inbox_size() == 1

    def test_dispatch_to_explicit_target(self):
        coordinator, agents = _coordinator_with_agents("Alpha", "Beta")
        target = coordinator.dispatch_task(
            {"job": "run"}, target_agent_id="beta"
        )
        assert target == "beta"

    def test_dispatch_any_online_agent(self):
        coordinator, agents = _coordinator_with_agents("Alpha", "Beta")
        target = coordinator.dispatch_task({"job": "anything"})
        assert target in {"alpha", "beta"}

    def test_dispatch_returns_none_no_capable_agent(self):
        coordinator, _ = _coordinator_with_agents("Alpha")
        target = coordinator.dispatch_task(
            {"job": "fly"}, required_capability="quantum"
        )
        assert target is None

    def test_dispatch_prefers_less_busy_agent(self):
        coordinator = SwarmCoordinator()
        busy = Agent("Busy", capabilities=["work"], agent_id="busy")
        idle = Agent("Idle", capabilities=["work"], agent_id="idle")
        coordinator.register_agent(busy)
        coordinator.register_agent(idle)
        # Preload busy agent's inbox
        for _ in range(5):
            coordinator.dispatch_task({"x": 1}, target_agent_id="busy")
        target = coordinator.dispatch_task({"x": 2}, required_capability="work")
        assert target == "idle"


class TestMessaging:
    def test_send_message_unicast(self):
        coordinator, agents = _coordinator_with_agents("Alpha", "Beta")
        result = coordinator.send_message(
            "alpha", "beta", MessageType.DATA, payload="hello"
        )
        assert result is True
        assert agents["Beta"].inbox_size() == 1

    def test_broadcast_reaches_all_except_sender(self):
        coordinator, agents = _coordinator_with_agents("A", "B", "C")
        count = coordinator.broadcast_message(MessageType.STATUS, sender_id="a")
        assert count == 2

    def test_publish_to_topic(self):
        coordinator, agents = _coordinator_with_agents("A", "B", "C")
        coordinator.subscribe_agent_to_topic("b", "news")
        coordinator.subscribe_agent_to_topic("c", "news")
        count = coordinator.publish_to_topic("news", payload="update")
        assert count == 2
        assert agents["B"].inbox_size() == 1
        assert agents["C"].inbox_size() == 1

    def test_subscribe_handler_invoked(self):
        received = []
        coordinator, agents = _coordinator_with_agents("A")
        coordinator.subscribe_handler_to_topic(
            "alerts", lambda m: received.append(m)
        )
        coordinator.publish_to_topic("alerts", payload="fire!")
        assert len(received) == 1


class TestHeartbeat:
    def test_heartbeat_reaches_all_agents(self):
        coordinator, agents = _coordinator_with_agents("A", "B", "C")
        count = coordinator.send_heartbeat()
        assert count == 3


class TestNetworkManagement:
    def test_add_network_link(self):
        coordinator, agents = _coordinator_with_agents("A", "B")
        coordinator.add_network_link("a", "b")
        assert coordinator.topology.get_link("a", "b") is not None
        assert coordinator.topology.get_link("b", "a") is not None  # bidirectional

    def test_add_network_link_unidirectional(self):
        coordinator, agents = _coordinator_with_agents("A", "B")
        coordinator.add_network_link("a", "b", bidirectional=False)
        assert coordinator.topology.get_link("a", "b") is not None
        assert coordinator.topology.get_link("b", "a") is None

    def test_find_route(self):
        coordinator, agents = _coordinator_with_agents("A", "B", "C")
        coordinator.add_network_link("a", "b")
        coordinator.add_network_link("b", "c")
        path = coordinator.find_route("a", "c")
        assert path == ["a", "b", "c"]

    def test_find_route_no_path(self):
        coordinator, agents = _coordinator_with_agents("A", "B")
        assert coordinator.find_route("a", "b") is None


class TestSwarmStatus:
    def test_status_keys(self):
        coordinator, _ = _coordinator_with_agents("A", "B")
        status = coordinator.get_swarm_status()
        assert "total_agents" in status
        assert "status_breakdown" in status
        assert "agents" in status
        assert "network" in status
        assert "message_log_size" in status
        assert "timestamp" in status

    def test_status_agent_count(self):
        coordinator, _ = _coordinator_with_agents("A", "B", "C")
        status = coordinator.get_swarm_status()
        assert status["total_agents"] == 3

    def test_status_online_breakdown(self):
        coordinator, _ = _coordinator_with_agents("A", "B")
        status = coordinator.get_swarm_status()
        assert status["status_breakdown"].get("online", 0) == 2
