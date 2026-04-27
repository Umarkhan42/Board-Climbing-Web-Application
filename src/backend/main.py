from pathlib import Path
from fastapi import FastAPI, Depends, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import json

from climb import load_board, sample_grade_stats, run_ga

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent.parent.parent

DB_PATH = BASE_DIR / "kilter.db"
USERS_DB = BASE_DIR / "users.db"

def get_users_conn():
    conn = sqlite3.connect(USERS_DB)
    conn.row_factory = sqlite3.Row
    return conn


def get_current_user(x_user_email: str = Header(None)):
    if not x_user_email:
        raise HTTPException(status_code=401, detail="Not logged in")

    conn = get_users_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE email = ?", (x_user_email,))
    user = cur.fetchone()
    conn.close()

    if user is None:
        raise HTTPException(status_code=401, detail="User not found")

    return dict(user)


@app.post("/register")
def register(data: dict):
    email = data.get("email")
    name = data.get("name")

    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    if not name:
        name = email.split("@")[0]

    conn = get_users_conn()
    cur = conn.cursor()

    try:
        cur.execute(
            "INSERT INTO users (email, name) VALUES (?, ?)",
            (email, name),
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="User already exists")

    cur.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = dict(cur.fetchone())

    conn.close()

    return {
        "message": "User registered",
        "user": user,
    }


@app.post("/login")
def login(data: dict):
    email = data.get("email")

    if not email:
        raise HTTPException(status_code=400, detail="Email is required")

    conn = get_users_conn()
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cur.fetchone()

    conn.close()

    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "message": "Logged in",
        "user": dict(user),
    }


@app.get("/generate")
def generate(grade: str = "V5", angle: int = 40):
    board = load_board(DB_PATH)
    board.build_edges(max_hand_distance=180, max_foot_distance=90)

    target_stats = sample_grade_stats(
        db_path=DB_PATH,
        board=board,
        grade=grade,
        n=10,
        target_angle=angle,
    )

    best_dna, best_route = run_ga(
        db_path=DB_PATH,
        board=board,
        target_grade=grade,
        target_stats=target_stats,
        population_size=30,
        generations=100,
        mutation_rate=0.2,
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
                "y": h.y,
            }
            for h in best_route.holds
        ],
    }


@app.post("/save-climb")
def save_climb(data: dict, user=Depends(get_current_user)):
    climb_name = data.get("name", "generated")
    grade = data.get("grade")
    angle = data.get("angle")
    holds = data.get("holds")

    if holds is None:
        raise HTTPException(status_code=400, detail="Holds are required")

    conn = get_users_conn()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO saved_climbs 
        (user_id, climb_name, grade, angle, holds_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            user["id"],
            climb_name,
            grade,
            angle,
            json.dumps(holds),
        ),
    )

    conn.commit()
    climb_id = cur.lastrowid
    conn.close()

    return {
        "message": "Climb saved",
        "climb_id": climb_id,
    }


@app.get("/my-climbs")
def my_climbs(user=Depends(get_current_user)):
    conn = get_users_conn()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT *
        FROM saved_climbs
        WHERE user_id = ?
        ORDER BY created_at DESC
        """,
        (user["id"],),
    )

    rows = cur.fetchall()
    conn.close()

    climbs = []

    for row in rows:
        climb = dict(row)
        climb["holds"] = json.loads(climb["holds_json"])
        del climb["holds_json"]
        climbs.append(climb)

    return {
        "climbs": climbs,
    }