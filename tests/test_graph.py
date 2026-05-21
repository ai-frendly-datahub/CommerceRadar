from flomers_kg.graph import KnowledgeGraph
import pytest


def test_graph_neighbors():
    graph = KnowledgeGraph()
    graph.add_node("m1", "Manufacturer", name="제조사")
    graph.add_node("p1", "Product", name="상품")
    graph.add_edge("m1", "PRODUCES", "p1")
    assert graph.neighbors("m1", "PRODUCES") == ["p1"]


def test_graph_find_nodes():
    graph = KnowledgeGraph()
    graph.add_node("s1", "Seller", name="Tokyo Beauty Select")
    result = graph.find_nodes(node_type="Seller", keyword="beauty")
    assert len(result) == 1


def test_graph_rejects_edges_with_unknown_nodes():
    graph = KnowledgeGraph()
    graph.add_node("m1", "Manufacturer", name="제조사")

    with pytest.raises(ValueError, match="Unknown target node"):
        graph.add_edge("m1", "PRODUCES", "p1")

    with pytest.raises(ValueError, match="Unknown source node"):
        graph.add_edge("missing", "PRODUCES", "m1")


def test_graph_neighbors_can_filter_by_relation():
    graph = KnowledgeGraph()
    graph.add_node("p1", "Product")
    graph.add_node("t1", "Trend")
    graph.add_node("s1", "Seller")
    graph.add_edge("p1", "MATCHES_TREND", "t1")
    graph.add_edge("p1", "SOLD_BY", "s1")

    assert graph.neighbors("p1") == ["t1", "s1"]
    assert graph.neighbors("p1", "MATCHES_TREND") == ["t1"]


def test_graph_find_nodes_filters_type_and_keyword_misses():
    graph = KnowledgeGraph()
    graph.add_node("s1", "Seller", name="Tokyo Beauty Select")
    graph.add_node("p1", "Product", name="Hair Oil")

    assert graph.find_nodes(node_type="Distributor") == []
    assert graph.find_nodes(keyword="missing") == []
    assert graph.find_nodes(node_type="Seller", keyword="hair") == []
