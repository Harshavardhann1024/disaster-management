import { Link } from "react-router-dom";

export default function ZoneCard({ zone }: any) {
  const ratio = zone.detected_people / Math.max(zone.total_beds, 1);

  const color =
    ratio > 1 ? "border-red-500" :
    ratio > 0.7 ? "border-orange-400" :
    ratio > 0.3 ? "border-yellow-400" :
    "border-emerald-400";

  return (
    <div className={`rounded-xl border ${color} bg-slate-900/60 p-6`}>
      <h3 className="text-xl font-bold">{zone.name}</h3>

      <div className="mt-3 text-sm space-y-1">
        <p>👥 {zone.detected_people} people</p>
        <p>🛏 {zone.available_beds}/{zone.total_beds} beds</p>
        <p>⚠ Risk: <b>{zone.risk_level}</b></p>
      </div>

      <div className="mt-4 h-2 bg-slate-700 rounded-full">
        <div
          className="h-2 bg-red-500 rounded-full"
          style={{ width: `${Math.min(100, ratio * 100)}%` }}
        />
      </div>

      <Link
        to={`/zone/${zone.id}`}
        className="inline-block mt-4 text-cyan-400"
      >
        View Live Analytics →
      </Link>
    </div>
  );
}
