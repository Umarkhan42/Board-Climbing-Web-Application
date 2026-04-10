import sqlite3
import re
import random
from copy import deepcopy
import numpy as np
import pprint
import boardlib
from PIL import Image, ImageDraw
from boardgraph import HoldNode, MoveEdge, BoardGraph
from routegraph import RouteHold, Route

ROLES = {12: "START", 13: "MIDDLE", 14:"FINISH", 15:"FOOT-ONLY"}
FOOTHOLDS = {
    1133, 1135, 1137, 1139, 1141, 1143, 1145, 1147, 1149, 1151, 1153, 1155, 1157, 1159, 1161, 1163, 1165, 1166, 1630, 1573, 1516, 1459, 1402, 1345, 1288, 1231, 1169, 1634, 1577, 1520, 1463, 1406, 
    1349, 1292, 1235, 1171, 1173, 1228, 1285, 1342, 1399, 1456, 1513, 1570, 1627, 1637, 1580, 1523, 1466, 1409, 1352, 1295, 1238, 1175, 1624, 1567, 1510, 1453, 1396, 1339, 1282, 1225, 1177, 1640,
    1583, 1526, 1469, 1412, 1355, 1298, 1241, 1179, 1621, 1564, 1507, 1450, 1393, 1336, 1279, 1222, 1181, 1643, 1586, 1529, 1472, 1415, 1358, 1301, 1244, 1183, 1618, 1561, 1504, 1447, 1390, 1333,
    1276, 1219, 1185, 1646, 1589, 1532, 1475, 1418, 1361, 1304, 1247, 1187, 1615, 1558, 1501, 1444, 1387, 1330, 1273, 1216, 1189, 1649, 1592, 1535, 1478, 1421, 1364, 1307, 1250, 1191, 1612, 1555,
    1498, 1441, 1384, 1327, 1270, 1213, 1193, 1652, 1595, 1538, 1481, 1424, 1367, 1310, 1253, 1195, 1609, 1552, 1495, 1438, 1381, 1324, 1267, 1210, 1197}

# Gets a specific climb from the database
# TODO needs to get exact climb rather than a list of possible climbs with similar names
def get_climb(db_path: str, name: str):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    query = """
    SELECT 
        c.*,
        cs.display_difficulty,
        dg.boulder_name AS grade
    FROM climbs c
    LEFT JOIN climb_stats cs
        ON c.uuid = cs.climb_uuid
    LEFT JOIN difficulty_grades dg
        ON CAST(cs.display_difficulty AS INTEGER) = dg.difficulty
    WHERE c.name LIKE ?
    """

    cur.execute(query, (name,))
    rows = cur.fetchall()
    conn.close()

    return [dict(row) for row in rows]

# Gets all hold information from placement_id 
def get_hold_position(db_path, placement_id, role_id=None):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    query = """
    SELECT 
        placements.hole_id,   -- <== added
        holes.x,
        holes.y
    FROM placements
    JOIN holes 
        ON placements.hole_id = holes.id
    WHERE placements.id = ?
    """

    cur.execute(query, (placement_id,))
    row = cur.fetchone()
    conn.close()

    if row is None:
        return None

    hole_id, x, y = row

    return {
        "placement_id": placement_id,
        "hole_id": hole_id,
        "hold_type": "FOOT" if hole_id in FOOTHOLDS else "HAND",
        "role": ROLES.get(role_id, "UNKNOWN"),
        "x":x,
        "y":y
    }

# Loads all the holds from the 16x12 superwide kilterboard
def load_board(db_path: str) -> BoardGraph:
    graph = BoardGraph()

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    query = """
    SELECT id, x, y
    FROM holes
    WHERE id BETWEEN 1133 AND 1656
    """

    cur.execute(query)
    rows = cur.fetchall()
    conn.close()

    for hole_id, x, y in rows:
        graph.add_node(
            HoldNode(
                hole_id=hole_id,
                hold_type="FOOT" if hole_id in FOOTHOLDS else "HAND",
                x=x,
                y=y
            )
        )

    return graph

# Builds a route object from get_climb and holds from get_hold_position
def build_route_from_climb(db_path: str, climb: dict, board: BoardGraph) -> Route:
    route = Route(
        name=climb["name"],
        route_id=climb["uuid"],
        grade=climb["grade"],
        frame=climb["frames"],
        angle=climb["angle"] if climb["angle"] is not None else climb["stats_angle"],
        author=climb["setter_username"],
        holds=[]
    )

    for placement_id, role_id in route.parse_frames():
        info = get_hold_position(db_path, placement_id, role_id)

        if info is None:
            continue

        route.holds.append(
            RouteHold(
                placement_id=info["placement_id"],
                hole_id=info["hole_id"],
                role=info["role"],
                x=info["x"],
                y=info["y"]
            )
        )

    route.compute_metrics(board)
    return route

# Gets a random route at a given grade
def get_random_graded_route(db_path: str, grade: str, board: BoardGraph, layout_id: int = 1) -> Route:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    query = """
    SELECT 
        c.*,
        cs.display_difficulty,
        cs.angle AS stats_angle,
        dg.boulder_name AS grade
    FROM climbs c
    LEFT JOIN climb_stats cs
        ON c.uuid = cs.climb_uuid
    LEFT JOIN difficulty_grades dg
        ON CAST(cs.display_difficulty AS INTEGER) = dg.difficulty
    WHERE (dg.boulder_name = ? OR dg.boulder_name LIKE ?)
      AND c.layout_id = ?
    ORDER BY RANDOM()
    LIMIT 1
    """

    cur.execute(query, (grade, f"%/{grade}", layout_id))
    row = cur.fetchone()
    conn.close()

    if row is None:
        raise ValueError(f"No route found for grade {grade} and layout_id {layout_id}")

    climb = dict(row)
    return build_route_from_climb(db_path=db_path, climb=climb, board=board)

def print_route_summary(route: Route):
    print(f"Name: {route.name}")
    print(f"Grade: {route.grade}")
    print(f"Angle: {route.angle}")
    print(f"Total holds: {route.metrics.total_holds}")
    print(f"Hand holds: {route.metrics.total_hand_holds}")
    print(f"Foot holds: {route.metrics.total_foot_holds}")
    print(f"Total moves: {route.metrics.total_moves}")
    print(f"Total length: {route.metrics.total_length:.2f}")
    print(f"Average move size: {route.metrics.average_move_size:.2f}")
    print(f"Max move size: {route.metrics.max_move_size:.2f}")
    print("-" * 40)

def score_route(route: Route, target_stats: dict) -> float:
    if route.metrics is None:
        return -1e9

    score = 0.0

    score -= abs(route.metrics.total_holds - target_stats["avg_holds"])
    score -= abs(route.metrics.total_hand_holds - target_stats["avg_hand_holds"])
    score -= abs(route.metrics.total_foot_holds - target_stats["avg_foot_holds"])
    score -= abs(route.metrics.total_length - target_stats["avg_total_length"]) * 0.05
    score -= abs(route.metrics.average_move_size - target_stats["avg_move_size"]) * 0.1
    score -= abs(route.metrics.max_move_size - target_stats["avg_max_move"]) * 0.1

    if len(route.start_holds()) < 1:
        score -= 100
    if len(route.finish_holds()) < 1:
        score -= 100

    starts = route.start_holds()
    finishes = route.finish_holds()
    if starts and finishes:
        avg_start_y = sum(h.y for h in starts) / len(starts)
        avg_finish_y = sum(h.y for h in finishes) / len(finishes)
        if avg_finish_y > avg_start_y:
            score += 20
        else:
            score -= 50

    if len(route.used_hole_ids()) != len(route.holds):
        score -= 50

    return score

def sample_grade_stats(db_path: str, board: BoardGraph, grade: str, n: int = 30, layout_id: int = 1) -> dict:
    routes = [
        get_random_graded_route(db_path=db_path, grade=grade, board=board, layout_id=layout_id)
        for _ in range(n)
    ]

    return {
        "avg_holds": sum(r.metrics.total_holds for r in routes) / n,
        "avg_hand_holds": sum(r.metrics.total_hand_holds for r in routes) / n,
        "avg_foot_holds": sum(r.metrics.total_foot_holds for r in routes) / n,
        "avg_total_length": sum(r.metrics.total_length for r in routes) / n,
        "avg_move_size": sum(r.metrics.average_move_size for r in routes) / n,
        "avg_max_move": sum(r.metrics.max_move_size for r in routes) / n,
    }

def main():
    db_path = "kilter.db"
    target_grade = "V5"

    board = load_board(db_path=db_path)
    board.build_edges(max_hand_distance=180, max_foot_distance=90)

    for i in range(100):

        route = get_random_graded_route(db_path=db_path, grade=target_grade, board=board)

        print_route_summary(route=route)

if __name__ == "__main__":
    main()