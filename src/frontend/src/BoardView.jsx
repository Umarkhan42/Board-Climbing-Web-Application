import { boardPositions } from "./boardPositions";

const VIEWBOX = "0 0 1080 1170";

function roleColor(role) {
  if (role === "START") return "#00DD00";
  if (role === "FINISH") return "#FF00FF";
  if (role === "FOOT-ONLY") return "#FFA500";
  return "#00FFFF";
}

export default function BoardView({ holds = [] }) {
  const holdMap = new Map(holds.map((h) => [Number(h.hole_id), h]));

  return (
    <svg
      viewBox={VIEWBOX}
      width="100%"
      xmlns="http://www.w3.org/2000/svg"
      style={{ maxHeight: "750px", background: "#111", borderRadius: "12px" }}
    >
      <image href="/layout_big_holds.svg" width="1080" height="1170" />
      <image href="/layout_small_holds.svg" width="1080" height="1170" />

      {Object.entries(boardPositions).map(([id, pos]) => 
      {
            const activeHold = holdMap.get(Number(id));
            const active = Boolean(activeHold);
            const color = active ? roleColor(activeHold.role) : "transparent";

            return (
                <circle
                key={id}
                cx={pos.x}
                cy={pos.y}
                r={30}
                fill={color}
                stroke={color}
                strokeWidth="8"
                fillOpacity={active ? 0.35 : 0}
                />
            );
        })}
    </svg>
  );
}