import { Link } from "react-router-dom";
import { Users, BedDouble, AlertTriangle, CheckCircle } from "lucide-react";

type Zone = {
  id: number;
  name: string;
  detected_people: number;
  available_beds: number;
  total_beds: number;
  risk_level: string;
};

const riskClass = (risk: string) => {
  switch (risk) {
    case "Safe":
      return "risk-safe";
    case "Caution":
    case "Elevated":
      return "risk-caution";
    case "Severe":
      return "risk-severe";
    default:
      return "";
  }
};

export default function ZoneCard({ zone }: { zone: Zone }) {
  const usedBeds = zone.total_beds - zone.available_beds;
  const bedPercent =
    zone.total_beds > 0
      ? Math.min((usedBeds / zone.total_beds) * 100, 100)
      : 0;

  return (
    <div
      className={`glass rounded-2xl p-6 flex flex-col justify-between transition-all duration-300 ${riskClass(
        zone.risk_level
      )}`}
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-white">{zone.name}</h2>

        {zone.risk_level === "Safe" ? (
          <CheckCircle className="text-green-400" size={20} />
        ) : (
          <AlertTriangle
            className={
              zone.risk_level === "Severe"
                ? "text-red-400"
                : "text-yellow-400"
            }
            size={20}
          />
        )}
      </div>

      {/* Stats */}
      <div className="space-y-2 text-sm text-slate-300">
        <div className="flex items-center gap-2">
          <Users size={16} className="text-purple-400" />
          <span>{zone.detected_people} people</span>
        </div>

        <div className="flex items-center gap-2">
          <BedDouble size={16} className="text-cyan-400" />
          <span>
            {zone.available_beds}/{zone.total_beds} beds
          </span>
        </div>

        <div
          className={`flex items-center gap-2 font-medium ${
            zone.risk_level === "Safe"
              ? "text-green-400"
              : zone.risk_level === "Severe"
              ? "text-red-400"
              : "text-yellow-400"
          }`}
        >
          <AlertTriangle size={14} />
          Risk: {zone.risk_level}
        </div>
      </div>

      {/* Bed usage bar */}
      <div className="mt-4">
        <div className="h-2 rounded-full bg-slate-700 overflow-hidden">
          <div
            className={`h-full transition-all ${
              zone.risk_level === "Safe"
                ? "bg-green-400"
                : zone.risk_level === "Severe"
                ? "bg-red-400"
                : "bg-yellow-400"
            }`}
            style={{ width: `${bedPercent}%` }}
          />
        </div>
      </div>

      {/* Footer */}
      <Link
        to={`/zone/${zone.id}`}
        className="mt-4 text-sm text-cyan-300 hover:text-cyan-200 transition"
      >
        View Live Analytics →
      </Link>
    </div>
  );
}
