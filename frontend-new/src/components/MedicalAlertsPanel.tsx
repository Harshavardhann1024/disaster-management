import { HeartPulse, MapPin, CheckCircle2 } from "lucide-react";

export default function MedicalAlertsPanel({ alerts }: { alerts: any[] }) {
  const hasAlerts = alerts && alerts.length > 0;

  return (
    <div className="rounded-xl border border-rose-500/40 bg-rose-500/10 p-6 shadow-lg shadow-rose-500/5">
      <div className="flex items-center gap-3 mb-4">
        <HeartPulse className="text-rose-400 w-6 h-6 animate-pulse" />
        <h3 className="text-xl font-bold text-rose-400">💗 Live Medical Emergencies</h3>
        <span className="ml-auto text-xs text-slate-400">
          Arduino Hardware Monitor
        </span>
      </div>

      {!hasAlerts ? (
        /* ── Empty state ── */
        <div className="flex items-center gap-3 py-6 px-4 rounded-lg border border-emerald-500/20 bg-emerald-500/5">
          <CheckCircle2 className="text-emerald-400 w-5 h-5 flex-shrink-0" />
          <div>
            <p className="text-sm font-medium text-emerald-300">No active medical emergencies</p>
            <p className="text-xs text-slate-500 mt-0.5">
              Hardware monitor is live — waiting for Arduino on COM13
            </p>
          </div>
        </div>
      ) : (
        /* ── Alert cards ── */
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
          {alerts.map((alert) => {
            const isAbnormal = alert.status === "ABNORMAL";
            return (
              <div
                key={alert.id}
                className={`p-4 rounded-lg border ${
                  isAbnormal
                    ? "border-rose-500/30 bg-rose-500/20"
                    : "border-emerald-500/30 bg-emerald-500/10"
                }`}
              >
                {/* Header row */}
                <div className="flex justify-between items-start mb-2">
                  <span className="font-semibold text-slate-200">{alert.zone_name}</span>
                  <span
                    className={`px-2 py-1 text-xs font-bold rounded-full ${
                      isAbnormal
                        ? "bg-rose-500/20 text-rose-300"
                        : "bg-emerald-500/20 text-emerald-300"
                    }`}
                  >
                    {alert.status}
                  </span>
                </div>

                {/* BPM reading */}
                <div className="text-3xl font-bold mb-3 flex items-end gap-2">
                  <span className={isAbnormal ? "text-rose-400" : "text-emerald-400"}>
                    {alert.bpm}
                  </span>
                  <span className="text-sm font-normal text-slate-400 mb-1">BPM</span>
                </div>

                {/* Location */}
                {alert.latitude && alert.longitude ? (
                  <div className="flex items-center gap-2 text-xs text-slate-400">
                    <MapPin className="w-3 h-3" />
                    <span>{Number(alert.latitude).toFixed(4)}, {Number(alert.longitude).toFixed(4)}</span>
                  </div>
                ) : (
                  <div className="flex items-center gap-2 text-xs text-slate-500">
                    <MapPin className="w-3 h-3" />
                    <span>GPS Fix Pending</span>
                  </div>
                )}

                {/* Timestamp */}
                <div className="mt-2 text-xs text-slate-500 text-right">
                  {new Date(alert.created_at).toLocaleTimeString()}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
