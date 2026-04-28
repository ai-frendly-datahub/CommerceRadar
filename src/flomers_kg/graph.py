from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Edge:
    source: str
    relation: str
    target: str
    metadata: dict[str, Any] = field(default_factory=dict)


class KnowledgeGraph:
    def __init__(self) -> None:
        self.nodes: dict[str, dict[str, Any]] = {}
        self.edges: list[Edge] = []

    def add_node(self, node_id: str, node_type: str, **properties: Any) -> None:
        self.nodes[node_id] = {"type": node_type, **properties}

    def add_edge(self, source: str, relation: str, target: str, **metadata: Any) -> None:
        if source not in self.nodes:
            raise ValueError(f"Unknown source node: {source}")
        if target not in self.nodes:
            raise ValueError(f"Unknown target node: {target}")
        self.edges.append(Edge(source=source, relation=relation, target=target, metadata=metadata))

    def neighbors(self, node_id: str, relation: str | None = None) -> list[str]:
        result = []
        for edge in self.edges:
            if edge.source == node_id and (relation is None or edge.relation == relation):
                result.append(edge.target)
        return result

    def find_nodes(self, node_type: str | None = None, keyword: str | None = None) -> list[tuple[str, dict[str, Any]]]:
        output = []
        kw = keyword.lower() if keyword else None
        for node_id, props in self.nodes.items():
            if node_type and props.get("type") != node_type:
                continue
            if kw:
                haystack = " ".join(str(v) for v in props.values()).lower()
                if kw not in haystack:
                    continue
            output.append((node_id, props))
        return output
