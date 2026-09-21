import { useState } from "react";
import BoardView from "./BoardView";

const API = "https://board-climbing-web-application.onrender.com";

export default function App() {
  const [activeTab, setActiveTab] = useState("generate");

  const [user, setUser] = useState(null);
  const [email, setEmail] = useState("");

  const [grade, setGrade] = useState("V5");
  const [angle, setAngle] = useState(40);
  const [route, setRoute] = useState(null);

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");

  const [savedClimbs, setSavedClimbs] = useState([]);

  const [searchName, setSearchName] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);

  const handleRegister = async () => {
    setMessage("");

    try {
      const res = await fetch(`${API}/register`, {
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
    } catch (err) {
      console.error(err);
      setMessage("Register error");
    }
  };

  const handleLogin = async () => {
    setMessage("");

    try {
      const res = await fetch(`${API}/login`, {
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
    } catch (err) {
      console.error(err);
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

    console.log("sending generate request:", { grade, angle });

    try {
      const res = await fetch(`${API}/generate?grade=${grade}&angle=${angle}`);
      const data = await res.json();

      console.log("generate response:", data);

      if (!res.ok) {
        setMessage(data.detail || "Failed to generate route");
        return;
      }

      setRoute(data);
    } catch (err) {
      console.error(err);
      setMessage("Failed to generate route");
    }

    setLoading(false);
  };

  const saveClimb = async () => {
    if (!route || !user) {
      setMessage("Login first before saving climbs");
      return;
    }

    setMessage("");

    try {
      const res = await fetch(`${API}/save-climb`, {
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
    } catch (err) {
      console.error(err);
      setMessage("Save climb error");
    }
  };

  const loadMyClimbs = async () => {
    if (!user) {
      setMessage("Please login to view your climbs");
      return;
    }

    setMessage("");

    try {
      const res = await fetch(`${API}/my-climbs`, {
        headers: { "X-User-Email": user.email },
      });

      const data = await res.json();

      if (!res.ok) {
        setMessage(data.detail || "Failed to load climbs");
        return;
      }

      setSavedClimbs(data.climbs || []);
    } catch (err) {
      console.error(err);
      setMessage("Load climbs error");
    }
  };

  const searchDatabaseClimbs = async () => {
    if (!searchName.trim()) {
      setMessage("Enter a climb name to search");
      return;
    }

    setSearchLoading(true);
    setMessage("");

    try {
      const res = await fetch(
        `${API}/search-climbs?name=${encodeURIComponent(searchName)}`
      );

      const data = await res.json();

      console.log("find climb response:", data);

      if (!res.ok) {
        setMessage(data.detail || "Search failed");
        return;
      }

      setSearchResults(data.climbs || []);
    } catch (err) {
      console.error(err);
      setMessage("Search error");
    }

    setSearchLoading(false);
  };

  const loadDatabaseClimb = async (climb) => {
  setMessage("");

  try {
    const res = await fetch("http://127.0.0.1:8000/load-climbs", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        uuid: climb.uuid,
        name: climb.name,
      }),
    });

    const data = await res.json();
    console.log("loaded database climb:", data);

    if (!res.ok) {
      setMessage(data.detail || "Failed to load climb");
      return;
    }

    setRoute(data);
    setMessage(`Loaded ${data.name}`);
  } catch (err) {
    console.error("load database climb error:", err);
    setMessage("Failed to load database climb");
  }
  };

  const loadSavedRoute = (climb) => {
    setRoute({
      name: climb.climb_name,
      grade: climb.grade,
      angle: climb.angle,
      holds: climb.holds,
    });

    setMessage(`Loaded ${climb.climb_name}`);
  };

  return (
    <div style={styles.page}>
      <div style={styles.header}>
        <div>
          <h1 style={styles.title}>Kilterboard Route Generator</h1>
          <p style={styles.subtitle}>Generate, search and save board climbs</p>
        </div>

        <div style={styles.loginBox}>
          <input
            style={styles.input}
            type="email"
            placeholder="Enter email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />

          {!user ? (
            <>
              <button style={styles.button} onClick={handleLogin}>
                Login
              </button>
              <button style={styles.secondaryButton} onClick={handleRegister}>
                Register
              </button>
            </>
          ) : (
            <>
              <span style={styles.userText}>{user.email}</span>
              <button style={styles.dangerButton} onClick={handleLogout}>
                Logout
              </button>
            </>
          )}
        </div>
      </div>

      <div style={styles.tabs}>
        <button
          style={activeTab === "generate" ? styles.activeTab : styles.tab}
          onClick={() => setActiveTab("generate")}
        >
          Generate Climbs
        </button>

        <button
          style={activeTab === "find" ? styles.activeTab : styles.tab}
          onClick={() => setActiveTab("find")}
        >
          Find Climb
        </button>

        <button
          style={activeTab === "popular" ? styles.activeTab : styles.tab}
          onClick={() => setActiveTab("popular")}
        >
          Popular Climbs
        </button>

        <button
          style={activeTab === "my" ? styles.activeTab : styles.tab}
          onClick={() => {
            if (!user) {
              setMessage("Please login to view your climbs");
              return;
            }

            setActiveTab("my");
            loadMyClimbs();
          }}
        >
          My Climbs
        </button>
      </div>

      {message && <div style={styles.message}>{message}</div>}

      <div style={styles.layout}>
        <div style={styles.leftPanel}>
          {activeTab === "generate" && (
            <div style={styles.card}>
              <h2>Generate Climb</h2>

              <div style={styles.formRow}>
                <div>
                  <label style={styles.label}>Grade</label>
                  <input
                    style={styles.input}
                    value={grade}
                    onChange={(e) => setGrade(e.target.value)}
                  />
                </div>

                <div>
                  <label style={styles.label}>Angle</label>
                  <input
                    style={styles.input}
                    type="number"
                    value={angle}
                    onChange={(e) => setAngle(Number(e.target.value))}
                  />
                </div>
              </div>

              <button
                style={styles.button}
                onClick={generateRoute}
                disabled={loading}
              >
                {loading ? "Generating..." : "Generate Route"}
              </button>

              {user && route && (
                <button style={styles.secondaryButton} onClick={saveClimb}>
                  Save Climb
                </button>
              )}
            </div>
          )}

          {activeTab === "find" && (
            <div style={styles.card}>
              <h2>Find Climb in Database</h2>

              <div style={styles.formRow}>
                <input
                  style={styles.input}
                  placeholder="Search climb name"
                  value={searchName}
                  onChange={(e) => setSearchName(e.target.value)}
                />

                <button
                  style={styles.button}
                  onClick={searchDatabaseClimbs}
                  disabled={searchLoading}
                >
                  {searchLoading ? "Searching..." : "Search"}
                </button>
              </div>

              <div style={styles.results}>
                {searchResults.map((climb) => (
                  <div key={climb.uuid} style={styles.climbCard}>
                    <p><b>Name:</b> {climb.name}</p>
                    <p><b>Grade:</b> {climb.grade || "Unknown"}</p>
                    <p><b>Angle:</b> {climb.angle || climb.stats_angle}</p>
                    <p><b>Setter:</b> {climb.setter_username}</p>

                    <button
                      style={styles.secondaryButton}
                      onClick={() => loadDatabaseClimb(climb)}
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
              <h2 style={{ marginTop: 0 }}>Popular Climbs</h2>

              <div style={styles.results}>
                {[
                  {
                    id: 1,
                    name: "Moonlight",
                    grade: "V5",
                    angle: 40,
                    setter: "Kilter",
                    description: "Classic compression climb with powerful moves.",
                    holds: [
                            {
                                "hole_id": 1148,
                                "role": "FOOT-ONLY",
                                "x": 80,
                                "y": 8
                            },
                            {
                                "hole_id": 1464,
                                "role": "START",
                                "x": 88,
                                "y": 32
                            },
                            {
                                "hole_id": 1511,
                                "role": "START",
                                "x": 96,
                                "y": 48
                            },
                            {
                                "hole_id": 1395,
                                "role": "MIDDLE",
                                "x": 64,
                                "y": 56
                            },
                            {
                                "hole_id": 1280,
                                "role": "FOOT-ONLY",
                                "x": 32,
                                "y": 64
                            },
                            {
                                "hole_id": 1391,
                                "role": "MIDDLE",
                                "x": 64,
                                "y": 80
                            },
                            {
                                "hole_id": 1305,
                                "role": "MIDDLE",
                                "x": 40,
                                "y": 96
                            },
                            {
                                "hole_id": 1386,
                                "role": "FOOT-ONLY",
                                "x": 64,
                                "y": 104
                            },
                            {
                                "hole_id": 1325,
                                "role": "MIDDLE",
                                "x": 48,
                                "y": 128
                            },
                            {
                                "hole_id": 1378,
                                "role": "FINISH",
                                "x": 64,
                                "y": 152
                            },
                            {
                                "hole_id": 1516,
                                "role": "FOOT-ONLY",
                                "x": 100,
                                "y": 20
                            },
                            {
                                "hole_id": 1456,
                                "role": "FOOT-ONLY",
                                "x": 84,
                                "y": 36
                            },
                            {
                                "hole_id": 1336,
                                "role": "FOOT-ONLY",
                                "x": 52,
                                "y": 68
                            }
                        ],
                  },
                  {
                    id: 2,
                    name: "Red Tide",
                    grade: "V7",
                    angle: 45,
                    setter: "Umar",
                    description: "Big dynamic moves with difficult tension.",
                    holds: [
                        {
                            "hole_id": 1148,
                            "role": "FOOT-ONLY",
                            "x": 80,
                            "y": 8
                        },
                        {
                            "hole_id": 1519,
                            "role": "START",
                            "x": 104,
                            "y": 24
                        },
                        {
                            "hole_id": 1508,
                            "role": "MIDDLE",
                            "x": 96,
                            "y": 64
                        },
                        {
                            "hole_id": 1392,
                            "role": "MIDDLE",
                            "x": 64,
                            "y": 72
                        },
                        {
                            "hole_id": 1551,
                            "role": "FINISH",
                            "x": 112,
                            "y": 136
                        },
                        {
                            "hole_id": 1137,
                            "role": "FOOT-ONLY",
                            "x": 124,
                            "y": 4
                        },
                        {
                            "hole_id": 1513,
                            "role": "FOOT-ONLY",
                            "x": 100,
                            "y": 36
                        },
                        {
                            "hole_id": 1561,
                            "role": "FOOT-ONLY",
                            "x": 116,
                            "y": 84
                        }
                    ],
                  },
                  {
                    id: 4,
                    name: "Night Shift",
                    grade: "V6",
                    angle: 40,
                    setter: "Kilter",
                    description: "Power endurance route with long movement chains.",
                    holds: [
                            {
                                "hole_id": 1289,
                                "role": "FOOT-ONLY",
                                "x": 32,
                                "y": 16
                            },
                            {
                                "hole_id": 1297,
                                "role": "START",
                                "x": 40,
                                "y": 56
                            },
                            {
                                "hole_id": 1508,
                                "role": "MIDDLE",
                                "x": 96,
                                "y": 64
                            },
                            {
                                "hole_id": 1389,
                                "role": "MIDDLE",
                                "x": 64,
                                "y": 88
                            },
                            {
                                "hole_id": 1476,
                                "role": "MIDDLE",
                                "x": 88,
                                "y": 96
                            },
                            {
                                "hole_id": 1557,
                                "role": "MIDDLE",
                                "x": 112,
                                "y": 104
                            },
                            {
                                "hole_id": 1485,
                                "role": "FINISH",
                                "x": 88,
                                "y": 152
                            },
                            {
                                "hole_id": 1513,
                                "role": "FOOT-ONLY",
                                "x": 100,
                                "y": 36
                            },
                            {
                                "hole_id": 1523,
                                "role": "FOOT-ONLY",
                                "x": 108,
                                "y": 44
                            },
                            {
                                "hole_id": 1567,
                                "role": "FOOT-ONLY",
                                "x": 116,
                                "y": 52
                            },
                            {
                                "hole_id": 1472,
                                "role": "FOOT-ONLY",
                                "x": 92,
                                "y": 76
                            },
                            {
                                "hole_id": 1535,
                                "role": "FOOT-ONLY",
                                "x": 108,
                                "y": 108
                            }
                        ],
                  },
                ].map((climb) => (
                  <div key={climb.id} style={styles.climbCard}>
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        marginBottom: "0.5rem",
                      }}
                    >
                      <h3 style={{ margin: 0 }}>{climb.name}</h3>

                      <span
                        style={{
                          background: "#0284c7",
                          padding: "0.25rem 0.6rem",
                          borderRadius: "999px",
                          fontSize: "0.85rem",
                          fontWeight: "bold",
                        }}
                      >
                        {climb.grade}
                      </span>
                    </div>

                    <p style={styles.muted}>
                      {climb.description}
                    </p>

                    <div
                      style={{
                        display: "flex",
                        gap: "1rem",
                        marginTop: "0.75rem",
                        color: "#cbd5e1",
                        fontSize: "0.9rem",
                        flexWrap: "wrap",
                      }}
                    >
                      <span>Angle: {climb.angle}°</span>
                      <span>Setter: {climb.setter}</span>
                    </div>

                    <div style={{ marginTop: "1rem" }}>
                      <button
                        style={styles.secondaryButton}
                        onClick={() => {
                          setRoute({
                            name: climb.name,
                            grade: climb.grade,
                            angle: climb.angle,
                            holds: climb.holds,
                          });

                          setMessage(`Loaded ${climb.name}`);
                        }}
                      >
                        Load Climb
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === "my" && (
            <div style={styles.card}>
              <h2>My Climbs</h2>

              <button style={styles.button} onClick={loadMyClimbs}>
                Refresh My Climbs
              </button>

              {savedClimbs.length === 0 && (
                <p style={styles.muted}>No saved climbs yet.</p>
              )}

              <div style={styles.results}>
                {savedClimbs.map((climb) => (
                  <div key={climb.id} style={styles.climbCard}>
                    <p><b>Name:</b> {climb.climb_name}</p>
                    <p><b>Grade:</b> {climb.grade}</p>
                    <p><b>Angle:</b> {climb.angle}</p>
                    <p><b>Created:</b> {climb.created_at}</p>

                    <button
                      style={styles.secondaryButton}
                      onClick={() => loadSavedRoute(climb)}
                    >
                      Load Climb
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}

          {route && (
            <div style={styles.card}>
              <h2>Current Climb</h2>
              <p><b>Name:</b> {route.name}</p>
              <p><b>Grade:</b> {route.grade}</p>
              <p><b>Angle:</b> {route.angle}</p>
            </div>
          )}
        </div>

        <div style={styles.boardPanel}>
          <BoardView holds={route?.holds ?? []} />
        </div>
      </div>
    </div>
  );
}

const styles = {
  page: {
  padding: "2rem",
  fontFamily: "Arial",
  color: "white",
  background: "linear-gradient(135deg, #020617, #111827)",
  minHeight: "100vh",
  width: "100%",
  margin: 0,
  },
  header: {
    display: "flex",
    justifyContent: "space-between",
    gap: "1rem",
    alignItems: "center",
    marginBottom: "1.5rem",
    flexWrap: "wrap",
  },
  title: {
    margin: 0,
    fontSize: "2rem",
  },
  subtitle: {
    marginTop: "0.4rem",
    color: "#94a3b8",
  },
  loginBox: {
    display: "flex",
    gap: "0.5rem",
    alignItems: "center",
    flexWrap: "wrap",
  },
  tabs: {
    display: "flex",
    gap: "0.75rem",
    marginBottom: "1rem",
    flexWrap: "wrap",
  },
  tab: {
    padding: "0.75rem 1rem",
    borderRadius: "999px",
    border: "1px solid #334155",
    background: "#0f172a",
    color: "#cbd5e1",
    cursor: "pointer",
  },
  activeTab: {
    padding: "0.75rem 1rem",
    borderRadius: "999px",
    border: "1px solid #38bdf8",
    background: "#0284c7",
    color: "white",
    cursor: "pointer",
  },
  layout: {
    display: "grid",
    gridTemplateColumns: "360px 1fr",
    gap: "1.5rem",
    alignItems: "start",
  },
  leftPanel: {
    display: "grid",
    gap: "1rem",
  },
  boardPanel: {
    background: "#020617",
    border: "1px solid #1e293b",
    borderRadius: "18px",
    padding: "1rem",
  },
  card: {
    background: "rgba(15, 23, 42, 0.95)",
    border: "1px solid #1e293b",
    borderRadius: "18px",
    padding: "1rem",
    boxShadow: "0 10px 30px rgba(0,0,0,0.25)",
  },
  formRow: {
    display: "flex",
    gap: "0.75rem",
    flexWrap: "wrap",
    marginBottom: "1rem",
  },
  label: {
    display: "block",
    marginBottom: "0.35rem",
    color: "#cbd5e1",
    fontSize: "0.9rem",
  },
  input: {
    padding: "0.65rem 0.75rem",
    borderRadius: "10px",
    border: "1px solid #334155",
    background: "#020617",
    color: "white",
    outline: "none",
  },
  button: {
    padding: "0.65rem 1rem",
    borderRadius: "10px",
    border: "none",
    background: "#22c55e",
    color: "#052e16",
    fontWeight: "bold",
    cursor: "pointer",
    marginRight: "0.5rem",
  },
  secondaryButton: {
    padding: "0.65rem 1rem",
    borderRadius: "10px",
    border: "1px solid #334155",
    background: "#1e293b",
    color: "white",
    cursor: "pointer",
    marginRight: "0.5rem",
  },
  dangerButton: {
    padding: "0.65rem 1rem",
    borderRadius: "10px",
    border: "none",
    background: "#ef4444",
    color: "white",
    cursor: "pointer",
  },
  message: {
    background: "#082f49",
    color: "#bae6fd",
    border: "1px solid #0369a1",
    padding: "0.75rem 1rem",
    borderRadius: "12px",
    marginBottom: "1rem",
  },
  results: {
    display: "grid",
    gap: "0.75rem",
    marginTop: "1rem",
  },
  climbCard: {
    background: "#020617",
    border: "1px solid #334155",
    borderRadius: "14px",
    padding: "1rem",
  },
  muted: {
    color: "#94a3b8",
  },
  userText: {
    color: "#93c5fd",
    fontWeight: "bold",
  },
};