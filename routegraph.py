from dataclasses import dataclass, field
from typing import List, Set, Optional
import re


@dataclass(frozen=True)
class RouteHold:
    placement_id: int
    hole_id: int
    role: str
    x: float
    y: float


@dataclass
class RouteMetrics:
    total_holds: int = 0
    total_hand_holds: int = 0
    total_foot_holds: int = 0
    total_moves: int = 0
    total_length: float = 0.0
    average_move_size: float = 0.0
    max_move_size: float = 0.0
    total_hold_difficulty: float = 0.0


@dataclass
class Route:
    name: str
    route_id: Optional[str]
    grade: Optional[str]
    frame: Optional[str] = None
    angle: Optional[int] = 40
    author: Optional[str] = None
    holds: List[RouteHold] = field(default_factory=list)
    metrics: Optional[RouteMetrics] = None

    def __str__(self):
        holds_with_coords = [f"{h.hole_id}:({h.x},{h.y})" for h in self.holds]
        return (
            f"Route(name={self.name}, \n"
            f"id={self.route_id}, \n"
            f"grade={self.grade}, \n"
            f"angle={self.angle}, \n"
            f"holds_with_coords={holds_with_coords}, \n"
            f"metrics={self.metrics})\n"
        )

    def start_holds(self) -> List[RouteHold]:
        return [h for h in self.holds if h.role == "START"]

    def finish_holds(self) -> List[RouteHold]:
        return [h for h in self.holds if h.role == "FINISH"]

    def middle_holds(self) -> List[RouteHold]:
        return [h for h in self.holds if h.role == "MIDDLE"]

    def foot_holds(self) -> List[RouteHold]:
        return [h for h in self.holds if h.role == "FOOT-ONLY"]

    def used_hole_ids(self) -> Set[int]:
        return {h.hole_id for h in self.holds}

    def parse_frames(self):
        if not self.frame:
            return []

        pairs = re.findall(r"p(\d+)r(\d+)", self.frame)
        return [(int(placement_id), int(role_id)) for placement_id, role_id in pairs]

    def compute_metrics(self, board) -> None:
        total_holds = len(self.holds)
        total_foot_holds = len(self.foot_holds())
        total_hand_holds = total_holds - total_foot_holds

        ordered_holds = [h for h in self.holds if h.role != "FOOT-ONLY"]

        total_length = 0.0
        move_sizes = []
        total_hold_difficulty = 0.0

        for hold in self.holds:
            node = board.get_node(hold.hole_id)
            total_hold_difficulty += node.difficulty

        for i in range(len(ordered_holds) - 1):
            a = ordered_holds[i]
            b = ordered_holds[i + 1]
            dist = board.distance_between(a.hole_id, b.hole_id)
            total_length += dist
            move_sizes.append(dist)

        self.metrics = RouteMetrics(
            total_holds=total_holds,
            total_hand_holds=total_hand_holds,
            total_foot_holds=total_foot_holds,
            total_moves=max(0, len(ordered_holds) - 1),
            total_length=total_length,
            average_move_size=(sum(move_sizes) / len(move_sizes)) if move_sizes else 0.0,
            max_move_size=max(move_sizes) if move_sizes else 0.0,
            total_hold_difficulty=total_hold_difficulty,
        )