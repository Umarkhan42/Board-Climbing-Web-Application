from dataclasses import dataclass
from collections import defaultdict
from typing import Dict, List, Set, Optional


@dataclass(frozen=True)
class HoldNode:
    hole_id: int
    hold_type: str   # "HAND" or "FOOT"
    x: int
    y: int


@dataclass
class MoveEdge:
    from_hold: int
    to_hold: int

    # Keep these optional for now until coordinates are added
    dist: Optional[float] = None
    dx: Optional[float] = None
    dy: Optional[float] = None
    reach_ratio: Optional[float] = None
    angle: Optional[float] = None

    move_type: str = "HAND"   # "HAND" or "FOOT"


class BoardGraph:
    def __init__(self):
        self.nodes: Dict[int, HoldNode] = {}

        self.hand_nodes: Set[int] = set()
        self.foot_nodes: Set[int] = set()

        self.hand_edges: Dict[int, List[MoveEdge]] = defaultdict(list)
        self.foot_edges: Dict[int, List[MoveEdge]] = defaultdict(list)

    def __str__(self):
        total_hand_edges = sum(len(v) for v in self.hand_edges.values())
        total_foot_edges = sum(len(v) for v in self.foot_edges.values())

        lines = []
        lines.append("BoardGraph")
        lines.append("-----------")
        lines.append(f"Total holds: {len(self.nodes)}")
        lines.append(f"Hand holds: {len(self.hand_nodes)}")
        lines.append(f"Foot holds: {len(self.foot_nodes)}")
        lines.append(f"Hand edges: {total_hand_edges}")
        lines.append(f"Foot edges: {total_foot_edges}")

        return "\n".join(lines)

    def add_node(self, node: HoldNode):
        self.nodes[node.hole_id] = node

        if node.hold_type == "FOOT":
            self.foot_nodes.add(node.hole_id)
        else:
            self.hand_nodes.add(node.hole_id)

    def get_node(self, hole_id: int) -> HoldNode:
        return self.nodes[hole_id]

    def add_edge(self, edge: MoveEdge):
        if edge.move_type == "FOOT":
            self.foot_edges[edge.from_hold].append(edge)
        else:
            self.hand_edges[edge.from_hold].append(edge)

    def is_hand_hold(self, hole_id: int) -> bool:
        return hole_id in self.hand_nodes

    def is_foot_hold(self, hole_id: int) -> bool:
        return hole_id in self.foot_nodes

    def get_hand_moves(self, hole_id: int) -> List[MoveEdge]:
        return self.hand_edges[hole_id]

    def get_foot_moves(self, hole_id: int) -> List[MoveEdge]:
        return self.foot_edges[hole_id]