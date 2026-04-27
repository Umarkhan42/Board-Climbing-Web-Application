import { useState } from "react";
import BoardView from "./BoardView";

export default function App() {
  const [user, setUser] = useState(null);
  const [email, setEmail] = useState("");
  const [grade, setGrade] = useState("V5");
  const [angle, setAngle] = useState(40);
  const [route, setRoute] = useState(null);
  const [loading, setLoading] = useState(false);
  const [savedClimbs, setSavedClimbs] = useState([]);
  const [message, setMessage] = useState("");

  const handleRegister = async () => {
    setMessage("");

    try {
      const res = await fetch("http://127.0.0.1:8000/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email,
          name: email.split("@")[0],
        }),
      });

      const data = await res.json();
      console.log("register response:", data);

      if (!res.ok) {
        setMessage(data.detail || "Register failed");
        return;
      }

      if (data.user) {
        setUser(data.user);
        setMessage("Registered and logged in");
      }
    } catch (err) {
      console.error("register error:", err);
      setMessage("Register error");
    }
  };

  const handleLogin = async () => {
    setMessage("");

    try {
      const res = await fetch("http://127.0.0.1:8000/login", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          email,
        }),
      });

      const data = await res.json();
      console.log("login response:", data);

      if (!res.ok) {
        setMessage(data.detail || "Login failed");
        return;
      }

      if (data.user) {
        setUser(data.user);
        setMessage("Logged in successfully");
      }
    } catch (err) {
      console.error("login error:", err);
      setMessage("Login error");
    }
  };

  const handleLogout = () => {
    setUser(null);
    setSavedClimbs([]);
    setMessage("Logged out");
  };

  const generateRoute = async () => {
    setLoading(true);
    setMessage("");

    console.log("sending generate request:", {
      grade,
      angle,
    });

    try {
      const res = await fetch(
        `http://127.0.0.1:8000/generate?grade=${grade}&angle=${angle}`
      );

      const data = await res.json();
      console.log("generate response:", data);

      setRoute(data);
    } catch (err) {
      console.error("generate route error:", err);
      setMessage("Failed to generate route");
    }

    setLoading(false);
  };

  const saveClimb = async () => {
    if (!route || !user) return;

    setMessage("");

    try {
      const res = await fetch("http://127.0.0.1:8000/save-climb", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-User-Email": user.email,
        },
        body: JSON.stringify({
          name: route.name,
          grade: route.grade,
          angle: route.angle,
          holds: route.holds,
        }),
      });

      const data = await res.json();
      console.log("save climb response:", data);

      if (!res.ok) {
        setMessage(data.detail || "Failed to save climb");
        return;
      }

      setMessage("Climb saved successfully");
      loadMyClimbs();
    } catch (err) {
      console.error("save climb error:", err);
      setMessage("Save climb error");
    }
  };

  const loadMyClimbs = async () => {
    if (!user) return;

    setMessage("");

    try {
      const res = await fetch("http://127.0.0.1:8000/my-climbs", {
        headers: {
          "X-User-Email": user.email,
        },
      });

      const data = await res.json();
      console.log("my climbs response:", data);

      if (!res.ok) {
        setMessage(data.detail || "Failed to load climbs");
        return;
      }

      setSavedClimbs(data.climbs || []);
      setMessage("Loaded saved climbs");
    } catch (err) {
      console.error("my climbs error:", err);
      setMessage("Load climbs error");
    }
  };

  const loadSavedRoute = (climb) => {
    setRoute({
      name: climb.climb_name,
      grade: climb.grade,
      angle: climb.angle,
      holds: climb.holds,
    });

    console.log("loaded saved climb into board:", climb);
    setMessage(`Loaded ${climb.climb_name}`);
  };

  return (
    <div
      style={{
        padding: "2rem",
        fontFamily: "Arial",
        color: "white",
        background: "#0b0b0b",
        minHeight: "100vh",
      }}
    >
      <h1>Kilterboard Route Generator</h1>

      <div
        style={{
          display: "flex",
          gap: "1rem",
          marginBottom: "1rem",
          flexWrap: "wrap",
          alignItems: "end",
        }}
      >
        <div>
          <label>Grade </label>
          <input value={grade} onChange={(e) => setGrade(e.target.value)} />
        </div>

        <div>
          <label>Angle </label>
          <input
            type="number"
            value={angle}
            onChange={(e) => setAngle(Number(e.target.value))}
          />
        </div>

        <button onClick={generateRoute} disabled={loading}>
          {loading ? "Generating..." : "Generate Route"}
        </button>

        {user && route && (
          <button onClick={saveClimb}>
            Save Climb
          </button>
        )}

        {user && (
          <button onClick={loadMyClimbs}>
            My Climbs
          </button>
        )}
      </div>

      {route && (
        <div style={{ marginBottom: "1rem" }}>
          <p><b>Name:</b> {route.name}</p>
          <p><b>Grade:</b> {route.grade}</p>
          <p><b>Angle:</b> {route.angle}</p>
        </div>
      )}

      {message && (
        <div style={{ marginBottom: "1rem", color: "#93c5fd" }}>
          {message}
        </div>
      )}

      <div style={{ width: "100%", maxWidth: "1000px", marginBottom: "1.5rem" }}>
        <BoardView holds={route?.holds ?? []} />
      </div>

      <div
        style={{
          marginTop: "1rem",
          display: "flex",
          gap: "0.5rem",
          alignItems: "center",
          flexWrap: "wrap",
          marginBottom: "1rem",
        }}
      >
        <input
          type="email"
          placeholder="Enter email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />

        <button onClick={handleRegister}>
          Register
        </button>

        <button onClick={handleLogin}>
          Login
        </button>

        {user && (
          <button onClick={handleLogout}>
            Logout
          </button>
        )}
      </div>

      {user && (
        <div style={{ marginBottom: "1rem" }}>
          <p><b>Logged in as:</b> {user.email}</p>
        </div>
      )}

      {savedClimbs.length > 0 && (
        <div style={{ marginTop: "2rem", maxWidth: "1000px" }}>
          <h2>Saved Climbs</h2>

          <div style={{ display: "grid", gap: "0.75rem" }}>
            {savedClimbs.map((climb) => (
              <div
                key={climb.id}
                style={{
                  background: "#111",
                  border: "1px solid #222",
                  borderRadius: "10px",
                  padding: "1rem",
                }}
              >
                <p><b>Name:</b> {climb.climb_name}</p>
                <p><b>Grade:</b> {climb.grade}</p>
                <p><b>Angle:</b> {climb.angle}</p>
                <p><b>Created:</b> {climb.created_at}</p>

                <button onClick={() => loadSavedRoute(climb)}>
                  Load Climb
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}