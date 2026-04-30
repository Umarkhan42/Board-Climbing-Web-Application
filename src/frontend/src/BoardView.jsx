import { boardPositions } from "./boardPositions";

const VIEWBOX_WIDTH = 1477;
const VIEWBOX_HEIGHT = 1200;
const HOLD_RADIUS = 30;

function roleColor(role) {
  if (role === "START") return "#00DD00";
  if (role === "FINISH") return "#FF00FF";
  if (role === "FOOT-ONLY") return "#FFA500";
  return "#00FFFF";
}

export default function BoardView({ holds = [] }) {
  const holdMap = new Map(holds.map((h) => [Number(h.hole_id), h]));

  return (
    <div
      style={{
        width: "100%",
        maxWidth: "1100px",
        margin: "0 auto",
      }}
    >
      <svg
        viewBox={`0 0 ${VIEWBOX_WIDTH} ${VIEWBOX_HEIGHT}`}
        xmlns="http://www.w3.org/2000/svg"
        style={{
          width: "100%",
          height: "auto",
          background: "#111",
          borderRadius: "12px",
          display: "block",
        }}
        preserveAspectRatio="xMidYMid meet"
      >
        <image href="/hand_holds.png" width={VIEWBOX_WIDTH} height={VIEWBOX_HEIGHT} />
        <image href="/foot_holds.png" width={VIEWBOX_WIDTH} height={VIEWBOX_HEIGHT} />

        {Object.entries(boardPositions).map(([id, pos]) => {
          const activeHold = holdMap.get(Number(id));
          const active = Boolean(activeHold);
          const color = active ? roleColor(activeHold.role) : "transparent";

          return (
            <circle
              key={pos.id}
              id={`hold-${pos.id}`}
              cx={pos.x}
              cy={pos.y}
              r={HOLD_RADIUS}
              fill={color}
              stroke={color}
              strokeWidth="8"
              fillOpacity={active ? 0.35 : 0}
              strokeOpacity={active ? 1 : 0}
            />
          );
        })}
      </svg>
    </div>
  );
}