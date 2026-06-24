import { AlertTriangle, ShieldCheck } from "lucide-react";

type AlertItem = {
  id: number;
  zone_name: string;
  level: "Caution" | "Elevated" | "Severe";
  message: string;
  created_at: string;
};

const levelStyles = {
  Caution:  { border: "border-yellow-500/30",  bg: "bg-yellow-500/10",  badge: "bg-yellow-500/20 text-yellow-300",  icon: "text-yellow-400" },
  Elevated: { border: "border-orange-500/30",  bg: "bg-orange-500/10",  badge: "bg-orange-500/20 text-orange-300",  icon: "text-orange-400" },
  Severe:   { border: "border-red-500/30",     bg: "bg-red-500/10",     badge: "bg-red-500/20 text-red-300",        icon: "text-red-400"    },
};

export default function AlertPanel({ alerts }: { alerts: AlertItem[] }) {
  const hasAlerts = alerts && alerts.length > 0;

  return (
    <div className="rounded-xl border border-red-500/40 bg-red-500/10 p-6">
      <div className="flex items-center gap-3 mb-4">
        <AlertTriangle className="text-red-400 w-6 h-6" />
        <h3 className="text-xl font-bold text-red-400">🔥 System Alerts</h3>
        {hasAlerts && (
          <span className="ml-auto text-xs bg-red-500/20 border border-red-500/30 text-red-300 px-2 py-0.5 rounded-full">
            {alerts.length} alert{alerts.length > 1 ? "s" : ""}
          </span>
        )}
      </div>

      {!hasAlerts ? (
        <div className="flex items-center gap-3 py-4 px-4 rounded-lg border border-emerald-500/20 bg-emerald-500/5">
          <ShieldCheck className="text-emerald-400 w-5 h-5 flex-shrink-0" />
          <div>
            <p className="text-sm font-medium text-emerald-300">No active alerts</p>
            <p className="text-xs text-slate-500 mt-0.5">All zones are within safe parameters</p>
          </div>
        </div>
      ) : (
        <ul className="space-y-2">
          {alerts.map((a) => {
            const style = levelStyles[a.level] ?? levelStyles.Severe;
            return (
              <li
                key={a.id}
                className={`flex items-start gap-3 p-3 rounded-lg border ${style.border} ${style.bg}`}
              >
                {/* Severity badge */}
                <span className={`mt-0.5 px-2 py-0.5 text-xs font-bold rounded-full flex-shrink-0 ${style.badge}`}>
                  {a.level}
                </span>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-slate-200">
                    <span className="font-semibold">{a.zone_name}</span>
                    {" — "}
                    <span className="text-slate-300">{a.message}</span>
                  </p>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {new Date(a.created_at).toLocaleTimeString()}
                  </p>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
