import sqlite3
import re
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

# Builds a route object from a route searchup in db
def build_route_from_climb(db_path: str, climb: dict) -> Route:
    route = Route(
        name=climb["name"],
        route_id=climb["uuid"],
        grade=climb["grade"],
        frame=climb["frames"],
        angle=climb["angle"],
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

    return route

# Gets a random route at a given grade
def get_random_graded_route(db_path: str, grade: str) -> Route:
    pass

def main():
    db_path = "kilter.db"
    climb_name = "Moonlight"
    climbs = get_climb(db_path=db_path, name=climb_name)

    climb = climbs[0]

    graph = load_board(db_path=db_path)
    route = build_route_from_climb(db_path=db_path, climb=climb)

    print(graph)
    print(route)

if __name__ == "__main__":
    main()