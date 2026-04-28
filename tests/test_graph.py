from flomers_kg.graph import KnowledgeGraph


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
