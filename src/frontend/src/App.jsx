import { useState } from "react";
import BoardView from "./BoardView";

export default function App() {
  const [grade, setGrade] = useState("V5");
  const [angle, setAngle] = useState(40);
  const [route, setRoute] = useState(null);
  const [loading, setLoading] = useState(false);

  const generateRoute = async () => {
    setLoading(true);

    try {
      const res = await fetch(
        `http://127.0.0.1:8000/generate?grade=${grade}&angle=${angle}`
      );
      const data = await res.json();
      setRoute(data);
    } catch (err) {
      console.error(err);
    }

    setLoading(false);
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

      <div style={{ display: "flex", gap: "1rem", marginBottom: "1rem" }}>
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
      </div>

      {route && (
        <div style={{ marginBottom: "1rem" }}>
          <p><b>Name:</b> {route.name}</p>
          <p><b>Grade:</b> {route.grade}</p>
          <p><b>Angle:</b> {route.angle}</p>
        </div>
      )}

      <div style={{ width: "100%", maxWidth: "1000px" }}>
        <BoardView holds={route?.holds ?? []} />
      </div>
    </div>
  );
}