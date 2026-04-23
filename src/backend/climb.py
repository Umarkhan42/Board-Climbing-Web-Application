import sqlite3
import random
import numpy as np
import math

from boardgraph import HoldNode, MoveEdge, BoardGraph
from routegraph import RouteHold, Route, RouteDNA
import matplotlib.pyplot as plt


ROLES = {12: "START", 13: "MIDDLE", 14:"FINISH", 15:"FOOT-ONLY"}
#TODO ADD THE NEW FOOTHOLDS 16X12
FOOTHOLDS = {
    1133, 1135, 1137, 1139, 1141, 1143, 1145, 1147, 1149, 1151, 1153, 1155, 1157, 1159, 1161, 1163, 1165, 1166, 1630, 1573, 1516, 1459, 1402, 1345, 1288, 1231, 1169, 1634, 1577, 1520, 1463, 1406, 
    1349, 1292, 1235, 1171, 1173, 1228, 1285, 1342, 1399, 1456, 1513, 1570, 1627, 1637, 1580, 1523, 1466, 1409, 1352, 1295, 1238, 1175, 1624, 1567, 1510, 1453, 1396, 1339, 1282, 1225, 1177, 1640,
    1583, 1526, 1469, 1412, 1355, 1298, 1241, 1179, 1621, 1564, 1507, 1450, 1393, 1336, 1279, 1222, 1181, 1643, 1586, 1529, 1472, 1415, 1358, 1301, 1244, 1183, 1618, 1561, 1504, 1447, 1390, 1333,
    1276, 1219, 1185, 1646, 1589, 1532, 1475, 1418, 1361, 1304, 1247, 1187, 1615, 1558, 1501, 1444, 1387, 1330, 1273, 1216, 1189, 1649, 1592, 1535, 1478, 1421, 1364, 1307, 1250, 1191, 1612, 1555,
    1498, 1441, 1384, 1327, 1270, 1213, 1193, 1652, 1595, 1538, 1481, 1424, 1367, 1310, 1253, 1195, 1609, 1552, 1495, 1438, 1381, 1324, 1267, 1210, 1197}
STAT_LIMITS = {
    "avg_holds": (3, 20),
    "avg_hand_holds": (1, 15),
    "avg_foot_holds": (0, 15),
    "avg_total_length": (20.0, 600.0),
    "avg_move_size": (5.0, 100.0),
    "avg_max_move": (10.0, 200.0),
    "target_angle": (0, 90),
}

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
        cs.angle AS stats_angle,
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
        placements.hole_id,
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
    WHERE 
        (id BETWEEN 1073 AND 1395)
        OR (id BETWEEN 1447 AND 1599)
        OR (id BETWEEN 4681 AND 4845)
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

        if info["hole_id"] not in board.nodes:
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

#TODO
def get_random_route(board: BoardGraph, number_of_holds=None) -> Route:
    pass

# Prints a summary of the route 
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

# Converts a route object to a DNA object
def route_to_dna(route: Route) -> RouteDNA:
    return RouteDNA(
        start_holds=[h.hole_id for h in route.start_holds()],
        hand_holds=[h.hole_id for h in route.middle_holds()],
        finish_holds=[h.hole_id for h in route.finish_holds()],
        foot_holds=[h.hole_id for h in route.foot_holds()],
    )

# Converts a DNA object to a Route object
def dna_to_route(dna: RouteDNA, board: BoardGraph, grade: str = None, angle: int = None) -> Route:
    holds = []

    for hole_id in dna.start_holds:
        node = board.get_node(hole_id)
        holds.append(RouteHold(
            placement_id=-1,
            hole_id=hole_id,
            role="START",
            x=node.x,
            y=node.y
        ))

    for hole_id in dna.hand_holds:
        node = board.get_node(hole_id)
        holds.append(RouteHold(
            placement_id=-1,
            hole_id=hole_id,
            role="MIDDLE",
            x=node.x,
            y=node.y
        ))

    for hole_id in dna.finish_holds:
        node = board.get_node(hole_id)
        holds.append(RouteHold(
            placement_id=-1,
            hole_id=hole_id,
            role="FINISH",
            x=node.x,
            y=node.y
        ))

    for hole_id in dna.foot_holds:
        node = board.get_node(hole_id)
        holds.append(RouteHold(
            placement_id=-1,
            hole_id=hole_id,
            role="FOOT-ONLY",
            x=node.x,
            y=node.y
        ))

    route = Route(
        name="generated",
        route_id=None,
        grade=grade,
        frame=None,
        angle=angle,
        author="GA",
        holds=holds
    )

    route.compute_metrics(board)
    return route

def average_position(hole_ids, board: BoardGraph):
    if not hole_ids:
        return None

    xs = [board.get_node(h).x for h in hole_ids]
    ys = [board.get_node(h).y for h in hole_ids]
    return (sum(xs) / len(xs), sum(ys) / len(ys))

def route_line_from_dna(dna: RouteDNA, board: BoardGraph):
    start_pos = average_position(dna.start_holds, board)
    finish_pos = average_position(dna.finish_holds, board)

    if start_pos is None or finish_pos is None:
        return None

    return (*start_pos, *finish_pos)

def unique_preserve_order(items):
    return list(dict.fromkeys(items))

# Calculates the fitness of the route
def calc_fitness(dna: RouteDNA, board: BoardGraph, target_stats: dict, target_grade: str = None) -> float:
    route = dna_to_route(dna,board,grade=target_grade,angle=target_stats["target_angle"])
    dna.fitness = score_route(route, target_stats)
    return dna.fitness

def enforce_start_finish_order(dna: RouteDNA, board: BoardGraph):
    if not dna.start_holds or not dna.finish_holds:
        return

    start_avg_y = sum(board.get_node(h).y for h in dna.start_holds) / len(dna.start_holds)
    finish_avg_y = sum(board.get_node(h).y for h in dna.finish_holds) / len(dna.finish_holds)

    # if starts are higher than finishes, swap them
    if start_avg_y < finish_avg_y:
        dna.start_holds, dna.finish_holds = dna.finish_holds, dna.start_holds

# Some footholds are anomalies this function fixes that
def fix_foot_holds(dna: RouteDNA, board: BoardGraph):
    if not dna.foot_holds:
        return

    hand_ids = dna.start_holds + dna.hand_holds + dna.finish_holds
    hand_nodes = [board.get_node(h) for h in hand_ids]

    foot_ids = list(board.foot_nodes)
    used = set(dna.start_holds + dna.hand_holds + dna.finish_holds + dna.foot_holds)

    new_feet = []

    # fix existing feet
    for foot_id in dna.foot_holds:
        node = board.get_node(foot_id)

        valid = any(
            node.y >= hand.y and abs(node.x - hand.x) <= 15
            for hand in hand_nodes
        )

        if valid:
            new_feet.append(foot_id)
            continue

        candidates = []
        for h in foot_ids:
            if h in used:
                continue

            cand = board.get_node(h)

            if any(cand.y >= hand.y and abs(cand.x - hand.x) <= 15 for hand in hand_nodes):
                candidates.append(h)

        if candidates:
            new_hole = random.choice(candidates)
            new_feet.append(new_hole)
            used.add(new_hole)
        else:
            new_feet.append(foot_id)

    new_feet = unique_preserve_order(new_feet)

    # add more feet if too few
    target_feet = max(1, len(hand_ids) // 2)

    if len(new_feet) < target_feet:
        candidates = []
        for h in foot_ids:
            if h in used:
                continue

            node = board.get_node(h)

            if any(node.y >= hand.y and abs(node.x - hand.x) <= 15 for hand in hand_nodes):
                candidates.append(h)

        random.shuffle(candidates)

        needed = target_feet - len(new_feet)

        for h in candidates[:needed]:
            new_feet.append(h)
            used.add(h)

    dna.foot_holds = unique_preserve_order(new_feet)

# Given 2 DNAs, merge them to create a child DNA 
def crossover(a: RouteDNA, b: RouteDNA, board: BoardGraph) -> RouteDNA:
    child_start = random.choice([a.start_holds[:], b.start_holds[:]])
    child_finish = random.choice([a.finish_holds[:], b.finish_holds[:]])

    if not child_start:
        child_start = a.start_holds[:] if a.start_holds else b.start_holds[:]
    if not child_finish:
        child_finish = a.finish_holds[:] if a.finish_holds else b.finish_holds[:]

    temp_child = RouteDNA(
        start_holds=unique_preserve_order(child_start),
        hand_holds=[],
        finish_holds=unique_preserve_order(child_finish),
        foot_holds=[],
    )

    # make sure starts are below finishes
    enforce_start_finish_order(temp_child, board)

    line = route_line_from_dna(temp_child, board)
    used = set(temp_child.start_holds + temp_child.finish_holds)

    hand_pool = unique_preserve_order(a.hand_holds + b.hand_holds)
    hand_pool = [h for h in hand_pool if h not in used]

    target_hand_count = max(len(a.hand_holds), len(b.hand_holds))

    if line is not None:
        x1, y1, x2, y2 = line
        hand_pool.sort(
            key=lambda h: point_to_line_distance(
                board.get_node(h).x,
                board.get_node(h).y,
                x1, y1, x2, y2
            )
        )

    child_hands = hand_pool[:target_hand_count]
    used.update(child_hands)

    foot_pool = unique_preserve_order(a.foot_holds + b.foot_holds)
    foot_pool = [h for h in foot_pool if h not in used]

    hand_positions = [
        board.get_node(h)
        for h in temp_child.start_holds + child_hands + temp_child.finish_holds
    ]

    valid_feet = []
    for h in foot_pool:
        node = board.get_node(h)
        if any(node.y >= hand.y and abs(node.x - hand.x) <= 150 for hand in hand_positions):
            valid_feet.append(h)

    target_foot_count = max(len(a.foot_holds), len(b.foot_holds))
    child_feet = valid_feet[:target_foot_count]

    child = RouteDNA(
        start_holds=unique_preserve_order(temp_child.start_holds),
        hand_holds=unique_preserve_order(child_hands),
        finish_holds=unique_preserve_order(temp_child.finish_holds),
        foot_holds=unique_preserve_order(child_feet),
    )

    enforce_start_finish_order(child, board)
    return child

# Mutation
def mutate(dna: RouteDNA, board: BoardGraph, mutation_rate: float = 0.1):
    used = set(dna.start_holds + dna.hand_holds + dna.finish_holds + dna.foot_holds)

    hand_ids = list(board.hand_nodes)
    foot_ids = list(board.foot_nodes)

    line = route_line_from_dna(dna, board)

    # mutate start holds
    for i in range(len(dna.start_holds)):
        if random.random() < mutation_rate:
            old = dna.start_holds[i]

            candidates = []
            for h in hand_ids:
                if h in used and h != old:
                    continue

                node = board.get_node(h)

                # starts should be LOWER on board
                if node.y < 700:
                    continue

                candidates.append(h)

            if candidates:
                new_hole = random.choice(candidates)
                used.discard(old)
                dna.start_holds[i] = new_hole
                used.add(new_hole)

    # mutate finish holds
    for i in range(len(dna.finish_holds)):
        if random.random() < mutation_rate:
            old = dna.finish_holds[i]

            candidates = []
            for h in hand_ids:
                if h in used and h != old:
                    continue

                node = board.get_node(h)

                # finishes should be HIGHER on board
                if node.y > 350:
                    continue

                candidates.append(h)

            if candidates:
                new_hole = random.choice(candidates)
                used.discard(old)
                dna.finish_holds[i] = new_hole
                used.add(new_hole)

    # force correct order after mutating start/finish
    enforce_start_finish_order(dna, board)

    line = route_line_from_dna(dna, board)

    # mutate middle hand holds
    for i in range(len(dna.hand_holds)):
        if random.random() < mutation_rate:
            old = dna.hand_holds[i]

            candidates = []
            for h in hand_ids:
                if h in used and h != old:
                    continue

                node = board.get_node(h)

                start_pos = average_position(dna.start_holds, board)
                finish_pos = average_position(dna.finish_holds, board)

                # do not allow handholds below the starts
                if start_pos is not None and node.y > start_pos[1] + 40:
                    continue

                # do not allow handholds above the finishes too much
                if finish_pos is not None and node.y < finish_pos[1] - 40:
                    continue

                if line is not None:
                    x1, y1, x2, y2 = line
                    dist = point_to_line_distance(node.x, node.y, x1, y1, x2, y2)
                    if dist > 80:
                        continue

                candidates.append(h)

            if candidates:
                if line is not None:
                    x1, y1, x2, y2 = line
                    candidates.sort(
                        key=lambda h: point_to_line_distance(
                            board.get_node(h).x,
                            board.get_node(h).y,
                            x1, y1, x2, y2
                        )
                    )
                    top_k = candidates[:max(1, min(10, len(candidates)))]
                    new_hole = random.choice(top_k)
                else:
                    new_hole = random.choice(candidates)

                used.discard(old)
                dna.hand_holds[i] = new_hole
                used.add(new_hole)

    hand_positions = [board.get_node(h) for h in dna.start_holds + dna.hand_holds + dna.finish_holds]

    # mutate foot holds
    for i in range(len(dna.foot_holds)):
        if random.random() < mutation_rate:
            old = dna.foot_holds[i]

            candidates = []
            for h in foot_ids:
                if h in used and h != old:
                    continue

                node = board.get_node(h)

                if any(node.y >= hand.y and abs(node.x - hand.x) <= 80 for hand in hand_positions):
                    candidates.append(h)

            if candidates:
                new_hole = random.choice(candidates)
                used.discard(old)
                dna.foot_holds[i] = new_hole
                used.add(new_hole)

    dna.start_holds = unique_preserve_order(dna.start_holds)
    dna.hand_holds = unique_preserve_order(dna.hand_holds)
    dna.finish_holds = unique_preserve_order(dna.finish_holds)
    dna.foot_holds = unique_preserve_order(dna.foot_holds)
    dna.start_holds, dna.finish_holds = dna.finish_holds, dna.finish_holds

    enforce_start_finish_order(dna, board)

# Run the Genetic Algorithm
def run_ga(db_path: str,board: BoardGraph,target_grade: str,target_stats: dict,population_size: int = 20,generations: int = 10,mutation_rate: float = 0.1):
    
    population = initial_dna_population(
        db_path=db_path,
        board=board,
        grade=target_grade,
        size=population_size
    )

    for gen in range(generations):
        for dna in population:
            calc_fitness(dna, board, target_stats, target_grade)

        population.sort(key=lambda d: d.fitness, reverse=True)
        print(f"Generation {gen}: best fitness = {population[0].fitness:.6f}")

        survivors = population[: population_size // 2]

        children = []
        while len(children) < population_size - len(survivors):
            parent_a = random.choice(survivors)
            parent_b = random.choice(survivors)

            child = crossover(parent_a, parent_b, board)
            mutate(child, board, mutation_rate)
            fix_foot_holds(child, board)
            children.append(child)

        population = survivors + children

    for dna in population:
        calc_fitness(dna, board, target_stats, target_grade)

    population.sort(key=lambda d: d.fitness, reverse=True)
    best_dna = population[0]
    best_route = dna_to_route(best_dna, board, grade=target_grade, angle=target_stats["target_angle"])

    return best_dna, best_route

# Initial population which is created by getting random routes at the grade given
def initial_dna_population(db_path: str, board: BoardGraph, grade: str, size: int = 20) -> list[RouteDNA]:
    population = []

    for _ in range(size):
        route = get_random_graded_route(db_path=db_path, grade=grade, board=board)
        population.append(route_to_dna(route))

    return population

# Is a valid route
def is_valid_route(route: Route) -> bool:
    return (
        route.metrics is not None
        and len(route.holds) > 0
        and len(route.start_holds()) >= 1
        and len(route.finish_holds()) >= 1
    )

# Distance from a point to the route line
def point_to_line_distance(px, py, x1, y1, x2, y2):
    dx = x2 - x1
    dy = y2 - y1

    if dx == 0 and dy == 0:
        return math.hypot(px - x1, py - y1)

    t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))

    nearest_x = x1 + t * dx
    nearest_y = y1 + t * dy

    return math.hypot(px - nearest_x, py - nearest_y)

# Used to determine the fitness of a route ie how close it is to the grade it was generated 
def score_route(route: Route, target_stats: dict) -> float:
    if route.metrics is None:
        return -1e9

    score = 0.0

    starts = route.start_holds()
    finishes = route.finish_holds()
    feet = route.foot_holds()
    hands = [h for h in route.holds if h.role in ("START", "MIDDLE", "FINISH")]
    middle_hands = route.middle_holds()

    # hard validity checks
    if len(starts) < 1:
        score -= 25
    if len(finishes) < 1:
        score -= 25
    if len(route.used_hole_ids()) != len(route.holds):
        score -= 15

    if not starts or not finishes:
        return score

    # metric matching
    score -= abs(route.metrics.total_holds - target_stats["avg_holds"]) * 0.8
    score -= abs(route.metrics.total_hand_holds - target_stats["avg_hand_holds"]) * 0.8
    score -= abs(route.metrics.total_foot_holds - target_stats["avg_foot_holds"]) * 0.8
    score -= abs(route.metrics.total_length - target_stats["avg_total_length"]) * 0.02
    score -= abs(route.metrics.average_move_size - target_stats["avg_move_size"]) * 0.04
    score -= abs(route.metrics.max_move_size - target_stats["avg_max_move"]) * 0.04

    # angle
    if route.angle is not None:
        angle_diff = abs(route.angle - target_stats["target_angle"])
        score -= angle_diff * 0.12
    else:
        score -= 2

    avg_start_x = sum(h.x for h in starts) / len(starts)
    avg_start_y = sum(h.y for h in starts) / len(starts)
    avg_finish_x = sum(h.x for h in finishes) / len(finishes)
    avg_finish_y = sum(h.y for h in finishes) / len(finishes)

    # starts should be low
    # larger y = lower
    if avg_start_y >= 700:
        score += min(6, (avg_start_y - 700) * 0.02)
    else:
        score -= min(6, (700 - avg_start_y) * 0.02)

    # finishes should be high
    # smaller y = higher
    if avg_finish_y <= 350:
        score += min(6, (350 - avg_finish_y) * 0.02)
    else:
        score -= min(6, (avg_finish_y - 350) * 0.02)

    # finish should be above start
    vertical_progress = avg_start_y - avg_finish_y
    if vertical_progress > 0:
        score += min(10, vertical_progress * 0.025)
    else:
        score -= 12

    # two starts should be close
    if len(starts) == 2:
        dx = starts[0].x - starts[1].x
        dy = starts[0].y - starts[1].y
        start_dist = math.hypot(dx, dy)

        if start_dist <= 120:
            score += 4
        else:
            score -= min(6, (start_dist - 120) * 0.03)

    # route should have a "plan":
    # middle hand holds should stay near the
    # line between start and finish

    if len(middle_hands) > 0:
        line_distances = [
            point_to_line_distance(
                h.x, h.y,
                avg_start_x, avg_start_y,
                avg_finish_x, avg_finish_y
            )
            for h in middle_hands
        ]

        avg_line_distance = sum(line_distances) / len(line_distances)

        # smaller is better
        if avg_line_distance <= 80:
            score += 6
        elif avg_line_distance <= 160:
            score += 2
        else:
            score -= (avg_line_distance - 160) * 0.03

    # penalise hand holds below the start
    # (excluding start holds themselves)

    hands_below_start = [h for h in middle_hands + finishes if h.y > avg_start_y]

    if hands_below_start:
        below_penalty = sum((h.y - avg_start_y) for h in hands_below_start)
        score -= min(10, below_penalty * 0.03)

    # footholds should generally be below nearby hands
    if feet and hands:
        good_feet = 0

        for foot in feet:
            if any(
                foot.y >= hand.y and abs(foot.x - hand.x) <= 150
                for hand in hands
            ):
                good_feet += 1

        foot_ratio = good_feet / len(feet)
        score += foot_ratio * 5
        score -= (1 - foot_ratio) * 3

    return score

# Gets a sample of n routes and finds the average statistics on them
def sample_grade_stats(db_path: str, board: BoardGraph, grade: str, n: int = 30, layout_id: int = 1, target_angle: int = 40) -> dict:

    print(f"Generating {n} sample grade stats for grade {grade}, angle {target_angle}")

    routes = []

    while len(routes) < n:
        route = get_random_graded_route(
            db_path=db_path,
            grade=grade,
            board=board,
            layout_id=layout_id
        )

        if route.angle is None:
            continue

        if abs(route.angle - target_angle) > 5:
            continue

        if is_valid_route(route):
            routes.append(route)
        
        print_route_summary(route=route)

    return {
        "avg_holds": sum(r.metrics.total_holds for r in routes) / n,
        "avg_hand_holds": sum(r.metrics.total_hand_holds for r in routes) / n,
        "avg_foot_holds": sum(r.metrics.total_foot_holds for r in routes) / n,
        "avg_total_length": sum(r.metrics.total_length for r in routes) / n,
        "avg_move_size": sum(r.metrics.average_move_size for r in routes) / n,
        "avg_max_move": sum(r.metrics.max_move_size for r in routes) / n,
        "target_angle": target_angle
    }

# Gets user defined stats
def get_user_target_stats() -> dict:
    print("Enter desired route characteristics:")

    avg_holds = get_bounded_input(
        "Total holds",
        *STAT_LIMITS["avg_holds"],
        cast_func=int
    )

    avg_hand_holds = get_bounded_input(
        "Hand holds",
        *STAT_LIMITS["avg_hand_holds"],
        cast_func=int
    )

    avg_foot_holds = get_bounded_input(
        "Foot holds",
        *STAT_LIMITS["avg_foot_holds"],
        cast_func=int
    )

    # extra logical check
    while avg_hand_holds + avg_foot_holds > avg_holds:
        print("Hand holds + foot holds cannot be greater than total holds.")
        avg_hand_holds = get_bounded_input(
            "Hand holds",
            *STAT_LIMITS["avg_hand_holds"],
            cast_func=int
        )
        avg_foot_holds = get_bounded_input(
            "Foot holds",
            *STAT_LIMITS["avg_foot_holds"],
            cast_func=int
        )

    avg_total_length = get_bounded_input(
        "Total length",
        *STAT_LIMITS["avg_total_length"]
    )

    avg_move_size = get_bounded_input(
        "Average move size",
        *STAT_LIMITS["avg_move_size"]
    )

    avg_max_move = get_bounded_input(
        "Max move size",
        *STAT_LIMITS["avg_max_move"]
    )

    while avg_max_move < avg_move_size:
        print("Max move size must be at least as large as average move size.")
        avg_max_move = get_bounded_input(
            "Max move size",
            *STAT_LIMITS["avg_max_move"]
        )

    target_angle = get_bounded_input(
        "Wall angle",
        *STAT_LIMITS["target_angle"],
        cast_func=int
    )

    return {
        "avg_holds": avg_holds,
        "avg_hand_holds": avg_hand_holds,
        "avg_foot_holds": avg_foot_holds,
        "avg_total_length": avg_total_length,
        "avg_move_size": avg_move_size,
        "avg_max_move": avg_max_move,
        "target_angle": target_angle,
    }

# Stops user from inputting invalid stats
def get_bounded_input(prompt: str, min_val: float, max_val: float, cast_func=float):
    while True:
        raw = input(f"{prompt} [{min_val} - {max_val}]: ").strip()

        try:
            value = cast_func(raw)
        except ValueError:
            print("Please enter a valid number.")
            continue

        if value < min_val or value > max_val:
            print(f"Value must be between {min_val} and {max_val}.")
            continue

        return value

# Evaluate the fitness function
def evaluate_fitness_across_grades(db_path, board):
    grades = ["V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8", "V9", "V10"]

    avg_scores = []

    for grade in grades:
        print(f"Evaluating {grade}...")

        # Get target stats for this grade
        target_stats = sample_grade_stats(db_path, board, grade, n=50)

        scores = []

        # Sample routes and score them
        for _ in range(50):
            try:
                route = get_random_graded_route(db_path, grade, board)
                score = score_route(route, target_stats)
                scores.append(score)
            except:
                continue  # skip broken routes

        if scores:
            avg_score = sum(scores) / len(scores)
        else:
            avg_score = 0

        avg_scores.append(avg_score)

        print(f"{grade}: avg score = {avg_score:.2f}")

    return grades, avg_scores

def plot_fitness(grades, scores):
    plt.figure()
    plt.plot(grades, scores, marker='o')

    plt.xlabel("Grade")
    plt.ylabel("Average Fitness Score")
    plt.title("Fitness Score vs Climbing Grade")

    plt.grid()
    plt.show()

def main():
    db_path = "kilter.db"
    target_grade = "V5"

    board = load_board(db_path=db_path)
    board.build_edges(max_hand_distance=180, max_foot_distance=90)

    route = get_random_route(board=board)
    route.compute_metrics(board=board)

    print_route_summary(route=route)
    print(route)

if __name__ == "__main__":
    main()