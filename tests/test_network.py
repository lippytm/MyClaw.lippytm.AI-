"""Tests for swarm.network module."""

import pytest

from swarm.network import ConnectionType, NetworkLink, NetworkTopology


class TestNetworkTopologyNodes:
    def setup_method(self):
        self.topo = NetworkTopology()

    def test_add_and_has_node(self):
        self.topo.add_node("a")
        assert self.topo.has_node("a") is True

    def test_remove_node(self):
        self.topo.add_node("a")
        self.topo.remove_node("a")
        assert self.topo.has_node("a") is False

    def test_list_nodes(self):
        self.topo.add_node("a")
        self.topo.add_node("b")
        assert set(self.topo.list_nodes()) == {"a", "b"}

    def test_node_count(self):
        for i in range(5):
            self.topo.add_node(str(i))
        assert self.topo.node_count() == 5

    def test_remove_node_removes_outgoing_links(self):
        self.topo.add_link(NetworkLink("a", "b"))
        self.topo.remove_node("a")
        assert self.topo.get_link("a", "b") is None

    def test_remove_node_removes_incoming_links(self):
        self.topo.add_link(NetworkLink("a", "b"))
        self.topo.remove_node("b")
        assert self.topo.get_link("a", "b") is None


class TestNetworkTopologyLinks:
    def setup_method(self):
        self.topo = NetworkTopology()
        self.topo.add_node("a")
        self.topo.add_node("b")

    def test_add_link_auto_registers_nodes(self):
        self.topo.add_link(NetworkLink("x", "y"))
        assert self.topo.has_node("x")
        assert self.topo.has_node("y")

    def test_get_link(self):
        link = NetworkLink("a", "b", ConnectionType.DIRECT, latency_ms=5.0)
        self.topo.add_link(link)
        assert self.topo.get_link("a", "b") is link

    def test_get_link_nonexistent_returns_none(self):
        assert self.topo.get_link("a", "z") is None

    def test_remove_link(self):
        self.topo.add_link(NetworkLink("a", "b"))
        assert self.topo.remove_link("a", "b") is True
        assert self.topo.get_link("a", "b") is None

    def test_remove_link_nonexistent_returns_false(self):
        assert self.topo.remove_link("a", "z") is False

    def test_link_count(self):
        self.topo.add_link(NetworkLink("a", "b"))
        self.topo.add_link(NetworkLink("b", "a"))
        assert self.topo.link_count() == 2

    def test_link_count_active_only(self):
        self.topo.add_link(NetworkLink("a", "b", is_active=True))
        self.topo.add_link(NetworkLink("b", "a", is_active=False))
        assert self.topo.link_count(active_only=True) == 1

    def test_set_link_active(self):
        self.topo.add_link(NetworkLink("a", "b", is_active=True))
        self.topo.set_link_active("a", "b", False)
        assert self.topo.get_link("a", "b").is_active is False

    def test_set_link_active_nonexistent_returns_false(self):
        assert self.topo.set_link_active("a", "z", True) is False


class TestNetworkTopologyNeighbours:
    def setup_method(self):
        self.topo = NetworkTopology()

    def test_direct_neighbours_active_only(self):
        self.topo.add_link(NetworkLink("a", "b", is_active=True))
        self.topo.add_link(NetworkLink("a", "c", is_active=False))
        assert self.topo.get_direct_neighbours("a") == ["b"]

    def test_no_neighbours_for_unknown_node(self):
        assert self.topo.get_direct_neighbours("z") == []


class TestNetworkTopologyPathFinding:
    def setup_method(self):
        # Build a simple graph: a-b-c-d with a shortcut a-d
        self.topo = NetworkTopology()
        links = [
            NetworkLink("a", "b"),
            NetworkLink("b", "a"),
            NetworkLink("b", "c"),
            NetworkLink("c", "b"),
            NetworkLink("c", "d"),
            NetworkLink("d", "c"),
            NetworkLink("a", "d"),
            NetworkLink("d", "a"),
        ]
        for link in links:
            self.topo.add_link(link)

    def test_same_node_path(self):
        assert self.topo.find_path("a", "a") == ["a"]

    def test_direct_connection(self):
        assert self.topo.find_path("a", "b") == ["a", "b"]

    def test_shortest_path_prefers_direct(self):
        # a→d is direct (1 hop) vs a→b→c→d (3 hops)
        path = self.topo.find_path("a", "d")
        assert path == ["a", "d"]

    def test_no_path_returns_none(self):
        self.topo.add_node("isolated")
        assert self.topo.find_path("a", "isolated") is None

    def test_inactive_links_not_followed(self):
        self.topo.set_link_active("a", "d", False)
        path = self.topo.find_path("a", "d")
        # Should route through b and c
        assert path is not None
        assert len(path) > 2

    def test_unknown_nodes_return_none(self):
        assert self.topo.find_path("x", "y") is None


class TestNetworkSummary:
    def test_summary_keys(self):
        topo = NetworkTopology()
        topo.add_link(NetworkLink("a", "b"))
        summary = topo.get_network_summary()
        assert set(summary.keys()) == {
            "node_count", "link_count", "active_link_count",
            "inactive_link_count", "nodes",
        }

    def test_to_dict(self):
        topo = NetworkTopology()
        topo.add_link(NetworkLink("a", "b"))
        d = topo.to_dict()
        assert "nodes" in d
        assert "links" in d
        assert len(d["links"]) == 1
