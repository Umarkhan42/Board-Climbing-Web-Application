from dataclasses import dataclass, field
from typing import List, Set, Optional
import re


@dataclass(frozen=True)
class RouteHold:
    placement_id: int
    hole_id: int
    role: str
    x: int
    y: int


@dataclass
class Route:
    name: str
    route_id: Optional[str]
    grade: Optional[str]
    frame: Optional[str] = None
    angle: Optional[int] = 40
    author: Optional[str] = None
    holds: List[RouteHold] = field(default_factory=list)

    def __str__(self):
        holds_with_coords = [f"{h.hole_id}:({h.x},{h.y})" for h in self.holds]

        return (
            f"Route(name={self.name}, "
            f"id={self.route_id}, "
            f"grade={self.grade}, "
            f"angle={self.angle}, "
            f"holds with coords={holds_with_coords}"
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
        """
        Extract (placement_id, role_id) pairs from this route's frame string.
        Example frame string:
            p1136r12p1200r13...

        Returns:
            [(placement_id, role_id), ...]
        """
        if not self.frame:
            return []

        pairs = re.findall(r"p(\d+)r(\d+)", self.frame)
        return [(int(placement_id), int(role_id)) for placement_id, role_id in pairs]