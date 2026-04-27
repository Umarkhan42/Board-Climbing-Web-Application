import { useState } from "react";
import BoardView from "./BoardView";

const API_URL = "http://127.0.0.1:8000";

const styles = {
  page: {
    minHeight: "100vh",
    background: "linear-gradient(135deg, #050505 0%, #111827 100%)",
    color: "white",
    fontFamily: "Inter, Arial, sans-serif",
    padding: "2rem",
  },
  container: {
    maxWidth: "1200px",
    margin: "0 auto",
  },
  header: {
    marginBottom: "1.5rem",
  },
  title: {
    fontSize: "2.2rem",
    margin: 0,
  },
  subtitle: {
    color: "#9ca3af",
    marginTop: "0.4rem",
  },
  tabs: {
    display: "flex",
    gap: "0.75rem",
    marginBottom: "1.5rem",
    flexWrap: "wrap",
  },
  tab: {
    padding: "0.75rem 1rem",
    borderRadius: "999px",
    border: "1px solid #374151",
    color: "white",
    cursor: "pointer",
  },
  card: {
    background: "rgba(17, 24, 39, 0.9)",
    border: "1px solid #1f2937",
    borderRadius: "18px",
    padding: "1.25rem",
    marginBottom: "1.25rem",
    boxShadow: "0 20px 40px rgba(0,0,0,0.25)",
  },
  row: {
    display: "flex",
    gap: "1rem",
    flexWrap: "wrap",
    alignItems: "end",
  },
  field: {
    display: "flex",
    flexDirection: "column",
    gap: "0.35rem",
  },
  label: {
    color: "#d1d5db",
    fontSize: "0.9rem",
  },
  input: {
    background: "#020617",
    border: "1px solid #374151",
    color: "white",
    borderRadius: "10px",
    padding: "0.7rem 0.8rem",
    outline: "none",
  },
  button: {
    background: "#2563eb",
    border: "none",
    color: "white",
    borderRadius: "10px",
    padding: "0.75rem 1rem",
    cursor: "pointer",
    fontWeight: "bold",
  },
  secondaryButton: {
    background: "#1f2937",
    border: "1px solid #374151",
    color: "white",
    borderRadius: "10px",
    padding: "0.75rem 1rem",
    cursor: "pointer",
  },
  message: {
    color: "#93c5fd",
    marginBottom: "1rem",
  },
  boardWrap: {
    width: "100%",
    maxWidth: "1000px",
    margin: "0 auto",
  },
};

export default function App() {
  const [activeTab, setActiveTab] = useState("generate");

  const [user, setUser] = useState(null);
  const [email, setEmail] = useState("");
  const [grade, setGrade] = useState("V5");
  const [angle, setAngle] = useState(40);
  const [route, setRoute] = useState(null);
  const [loading, setLoading] = useState(false);
  const [searchName, setSearchName] = useState("");
  const [databaseClimbs, setDatabaseClimbs] = useState([]);
  const [savedClimbs, setSavedClimbs] = useState([]);
  const [message, setMessage] = useState("");

  const tabButton = (id, label) => (
    <button
      onClick={() => setActiveTab(id)}
      style={{
        ...styles.tab,
        background: activeTab === id ? "#2563eb" : "#111827",
      }}
    >
      {label}
    </button>
  );

  const handleRegister = async () => {
    setMessage("");

    try {
      const res = await fetch(`${API_URL}/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, name: email.split("@")[0] }),
      });

      const data = await res.json();

      if (!res.ok) {
        setMessage(data.detail || "Register failed");
        return;
      }

      setUser(data.user);
      setMessage("Registered and logged in");
    } catch {
      setMessage("Register error");
    }
  };

  const handleLogin = async () => {
    setMessage("");

    try {
      const res = await fetch(`${API_URL}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });

      const data = await res.json();

      if (!res.ok) {
        setMessage(data.detail || "Login failed");
        return;
      }

      setUser(data.user);
      setMessage("Logged in successfully");
    } catch {
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

    try {
      const res = await fetch(`${API_URL}/generate?grade=${grade}&angle=${angle}`);
      const data = await res.json();
      setRoute(data);
    } catch {
      setMessage("Failed to generate route");
    }

    setLoading(false);
  };

  const saveClimb = async () => {
    if (!route || !user) return;

    try {
      const res = await fetch(`${API_URL}/save-climb`, {
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

      if (!res.ok) {
        setMessage(data.detail || "Failed to save climb");
        return;
      }

      setMessage("Climb saved successfully");
    } catch {
      setMessage("Save climb error");
    }
  };

  const loadMyClimbs = async () => {
    if (!user) return;

    try {
      const res = await fetch(`${API_URL}/my-climbs`, {
        headers: { "X-User-Email": user.email },
      });

      const data = await res.json();

      if (!res.ok) {
        setMessage(data.detail || "Failed to load climbs");
        return;
      }

      setSavedClimbs(data.climbs || []);
      setMessage("Loaded saved climbs");
    } catch {
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

    setActiveTab("generate");
    setMessage(`Loaded ${climb.climb_name}`);
  };

  const searchDatabaseClimbs = async () => {
  if (!searchName.trim()) return;

  setMessage("");

  try {
    const res = await fetch(
      `${API_URL}/search-climbs?name=${encodeURIComponent(searchName)}`
    );

    const data = await res.json();
    console.log("database climb search response:", data);

    if (!res.ok) {
      setMessage(data.detail || "Failed to search climbs");
      return;
    }

    setDatabaseClimbs(data.climbs || []);
    setMessage(`Found ${data.count} climb(s)`);
  } catch (err) {
    console.error("search climbs error:", err);
    setMessage("Search climbs error");
  }
};

  const loadDatabaseRoute = (climb) => {
    setRoute({
      name: climb.name,
      grade: climb.grade,
      angle: climb.angle,
      holds: climb.holds,
    });

    setActiveTab("generate");
    setMessage(`Loaded ${climb.name}`);
  };

  return (
    <div style={styles.page}>
      <div style={styles.container}>
        <div style={styles.header}>
          <h1 style={styles.title}>Kilterboard Route Generator</h1>
          <p style={styles.subtitle}>
            Generate, save and explore board climbs.
          </p>
        </div>

        <div style={styles.tabs}>
          {tabButton("generate", "Generate Climbs")}
          {tabButton("find", "Find Climb")}
          {tabButton("popular", "Popular Climbs")}
        </div>

        {message && <div style={styles.message}>{message}</div>}

        <div style={styles.card}>
          <div style={styles.row}>
            <div style={styles.field}>
              <label style={styles.label}>Email</label>
              <input
                style={styles.input}
                type="email"
                placeholder="Enter email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>

            <button style={styles.secondaryButton} onClick={handleRegister}>
              Register
            </button>

            <button style={styles.secondaryButton} onClick={handleLogin}>
              Login
            </button>

            {user && (
              <button style={styles.secondaryButton} onClick={handleLogout}>
                Logout
              </button>
            )}
          </div>

          {user && (
            <p style={{ color: "#9ca3af", marginBottom: 0 }}>
              Logged in as <b style={{ color: "white" }}>{user.email}</b>
            </p>
          )}
        </div>

        {activeTab === "generate" && (
          <>
            <div style={styles.card}>
              <div style={styles.row}>
                <div style={styles.field}>
                  <label style={styles.label}>Grade</label>
                  <input
                    style={styles.input}
                    value={grade}
                    onChange={(e) => setGrade(e.target.value)}
                  />
                </div>

                <div style={styles.field}>
                  <label style={styles.label}>Angle</label>
                  <input
                    style={styles.input}
                    type="number"
                    value={angle}
                    onChange={(e) => setAngle(Number(e.target.value))}
                  />
                </div>

                <button style={styles.button} onClick={generateRoute} disabled={loading}>
                  {loading ? "Generating..." : "Generate Route"}
                </button>

                {user && route && (
                  <button style={styles.secondaryButton} onClick={saveClimb}>
                    Save Climb
                  </button>
                )}
              </div>

              {route && (
                <div style={{ marginTop: "1rem", color: "#d1d5db" }}>
                  <p><b>Name:</b> {route.name}</p>
                  <p><b>Grade:</b> {route.grade}</p>
                  <p><b>Angle:</b> {route.angle}</p>
                </div>
              )}
            </div>

            <div style={styles.card}>
              <div style={styles.boardWrap}>
                <BoardView holds={route?.holds ?? []} />
              </div>
            </div>
          </>
        )}

        {activeTab === "find" && (
          <div style={styles.card}>
            <h2>Find Climb in Database</h2>

            <div style={styles.row}>
              <div style={styles.field}>
                <label style={styles.label}>Climb name</label>
                <input
                  style={styles.input}
                  placeholder="Search climb name..."
                  value={searchName}
                  onChange={(e) => setSearchName(e.target.value)}
                />
              </div>

              <button style={styles.button} onClick={searchDatabaseClimbs}>
                Search
              </button>
            </div>

            <div style={{ marginTop: "1rem", display: "grid", gap: "0.75rem" }}>
              {databaseClimbs.map((climb, index) => (
                <div
                  key={`${climb.name}-${index}`}
                  style={{
                    background: "#020617",
                    border: "1px solid #1f2937",
                    borderRadius: "12px",
                    padding: "1rem",
                  }}
                >
                  <p><b>Name:</b> {climb.name}</p>
                  <p><b>Grade:</b> {climb.grade}</p>
                  <p><b>Angle:</b> {climb.angle}</p>
                  <p><b>Author:</b> {climb.author}</p>
                  <p><b>Holds:</b> {climb.holds.length}</p>

                  <button
                    style={styles.secondaryButton}
                    onClick={() => loadDatabaseRoute(climb)}
                  >
                    Load Climb
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {activeTab === "popular" && (
          <div style={styles.card}>
            <h2>Popular Climbs</h2>
            <p style={{ color: "#9ca3af" }}>Popular climbs will go here later.</p>
          </div>
        )}
      </div>
    </div>
  );
}