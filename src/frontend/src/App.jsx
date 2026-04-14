import { useState } from "react";

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
    <div style={{ padding: "2rem", fontFamily: "Arial" }}>
      <h1>Kilterboard Route Generator</h1>

      <div>
        <label>Grade: </label>
        <input value={grade} onChange={(e) => setGrade(e.target.value)} />
      </div>

      <div>
        <label>Angle: </label>
        <input
          type="number"
          value={angle}
          onChange={(e) => setAngle(Number(e.target.value))}
        />
      </div>

      <button onClick={generateRoute} disabled={loading}>
        {loading ? "Generating..." : "Generate Route"}
      </button>

      {route && (
        <div style={{ marginTop: "2rem" }}>
          <h2>Generated Route</h2>
          <p><b>Grade:</b> {route.grade}</p>
          <p><b>Angle:</b> {route.angle}</p>

          <h3>Holds</h3>
          <ul>
            {route.holds.map((h, i) => (
              <li key={i}>
                {h.role} → ({h.x}, {h.y})
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}