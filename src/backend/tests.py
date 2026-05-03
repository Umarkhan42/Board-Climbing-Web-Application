import random
import matplotlib.pyplot as plt

from climb import load_board, get_random_graded_route, sample_grade_stats, run_ga

DB_PATH = "kilter.db"

SAMPLES_PER_GRADE = 25
GRADES = ["V1", "V2", "V3", "V4", "V5", "V6", "V7", "V8"]

TARGET_ANGLE = 40
ANGLE_TOLERANCE = 5


def route_stats(route):
    return {
        "total_holds": route.metrics.total_holds,
        "hand_holds": route.metrics.total_hand_holds,
        "foot_holds": route.metrics.total_foot_holds,
        "total_moves": route.metrics.total_moves,
        "total_length": route.metrics.total_length,
        "avg_move_size": route.metrics.average_move_size,
        "max_move_size": route.metrics.max_move_size,
    }

def average_stats(stats_list):
    keys = stats_list[0].keys()

    averages = {
        key: sum(stats[key] for stats in stats_list) / len(stats_list)
        for key in keys
    }

    return averages

def get_database_routes(board):
    print("Retrieving database climbs...")

    routes = []

    while len(routes) < SAMPLE_SIZE:
        grade = random.choice(GRADES)

        try:
            route = get_random_graded_route(
                db_path=DB_PATH,
                grade=grade,
                board=board,
            )

            if route.angle is None:
                print(f"Skipped {route.name} because angle is None")
                continue

            if abs(route.angle - TARGET_ANGLE) > ANGLE_TOLERANCE:
                print(
                    f"Skipped {route.name} because angle {route.angle} "
                    f"is outside tolerance"
                )
                continue

            routes.append(route)

            print(
                f"Retrieved {len(routes)}/{SAMPLE_SIZE} | "
                f"{route.name} | {route.grade} | angle={route.angle}"
            )

        except Exception as e:
            print(f"Database route error: {e}")

    print("Finished retrieving database climbs")
    return routes

def get_generated_routes(board):
    print("Generating climbs using GA...")

    routes = []

    while len(routes) < SAMPLE_SIZE:
        grade = random.choice(GRADES)

        try:
            print(f"Sampling target stats for {grade}")

            target_stats = sample_grade_stats(
                db_path=DB_PATH,
                board=board,
                grade=grade,
                n=10,
                target_angle=TARGET_ANGLE,
            )

            print(f"Running GA for {grade}")

            best_dna, route = run_ga(
                db_path=DB_PATH,
                board=board,
                target_grade=grade,
                target_stats=target_stats,
                population_size=20,
                generations=25,
                mutation_rate=0.15,
            )

            routes.append(route)

            print(
                f"Generated {len(routes)}/{SAMPLE_SIZE} | "
                f"{route.grade} | fitness={best_dna.fitness:.2f}"
            )

        except Exception as e:
            print(f"Generated route error: {e}")

    print("Finished generating climbs")
    return routes

def plot_grade_comparison(database_by_grade, generated_by_grade):
    metrics = [
        "total_holds",
        "hand_holds",
        "foot_holds",
        "total_moves",
        "total_length",
        "avg_move_size",
        "max_move_size",
    ]

    for metric in metrics:
        database_values = [
            database_by_grade[grade][metric]
            for grade in GRADES
        ]

        generated_values = [
            generated_by_grade[grade][metric]
            for grade in GRADES
        ]

        x = range(len(GRADES))
        width = 0.35

        plt.figure(figsize=(12, 6))

        plt.bar(
            [i - width / 2 for i in x],
            database_values,
            width,
            label="Database climbs"
        )

        plt.bar(
            [i + width / 2 for i in x],
            generated_values,
            width,
            label="Generated climbs"
        )

        plt.xticks(x, GRADES)
        plt.ylabel(metric)
        plt.title(f"{metric}: Generated vs Database Climbs at {TARGET_ANGLE}°")
        plt.legend()
        plt.tight_layout()
        plt.show()

def main():
    print("Loading board")
    board = load_board(DB_PATH)

    print("Building board edges")
    board.build_edges(max_hand_distance=180, max_foot_distance=90)

    database_by_grade = {}
    generated_by_grade = {}

    for grade in GRADES:
        print(f"Starting comparison for {grade}")

        database_routes = []
        generated_routes = []

        while len(database_routes) < SAMPLES_PER_GRADE:
            try:
                route = get_random_graded_route(
                    db_path=DB_PATH,
                    grade=grade,
                    board=board,
                )

                if route.angle is None:
                    continue

                if abs(route.angle - TARGET_ANGLE) > ANGLE_TOLERANCE:
                    continue

                database_routes.append(route)

                print(
                    f"{grade} database {len(database_routes)}/{SAMPLES_PER_GRADE}: "
                    f"{route.name}, angle={route.angle}"
                )

            except Exception as e:
                print(f"{grade} database error: {e}")

        target_stats = sample_grade_stats(
            db_path=DB_PATH,
            board=board,
            grade=grade,
            n=10,
            target_angle=TARGET_ANGLE,
        )

        while len(generated_routes) < SAMPLES_PER_GRADE:
            try:
                best_dna, route = run_ga(
                    db_path=DB_PATH,
                    board=board,
                    target_grade=grade,
                    target_stats=target_stats,
                    population_size=20,
                    generations=25,
                    mutation_rate=0.15,
                )

                generated_routes.append(route)

                print(
                    f"{grade} generated {len(generated_routes)}/{SAMPLES_PER_GRADE}: "
                    f"fitness={best_dna.fitness:.2f}"
                )

            except Exception as e:
                print(f"{grade} generated error: {e}")

        database_by_grade[grade] = average_stats(
            [route_stats(route) for route in database_routes]
        )

        generated_by_grade[grade] = average_stats(
            [route_stats(route) for route in generated_routes]
        )

    plot_grade_comparison(database_by_grade, generated_by_grade)

if __name__ == "__main__":
    main()