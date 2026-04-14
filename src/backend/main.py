from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from climb import (
    load_board,
    sample_grade_stats,
    run_ga,
)

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = BASE_DIR / "kilter.db"

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {"message": "Backend is running"}


@app.get("/generate")
def generate_route(grade: str = "V5", angle: int = 40):
    board = load_board(DB_PATH)
    board.build_edges(max_hand_distance=180, max_foot_distance=90)

    target_stats = sample_grade_stats(
        db_path=DB_PATH,
        board=board,
        grade=grade,
        n=15,
        target_angle=angle
    )

    best_dna, best_route = run_ga(
        db_path=DB_PATH,
        board=board,
        target_grade=grade,
        target_stats=target_stats,
        population_size=30,
        generations=50,
        mutation_rate=0.1
    )

    return {
        "name": best_route.name,
        "grade": best_route.grade,
        "angle": best_route.angle,
        "holds": [
            {
                "hole_id": h.hole_id,
                "role": h.role,
                "x": h.x,
                "y": h.y
            }
            for h in best_route.holds
        ]
    }