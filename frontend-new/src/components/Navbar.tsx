interface NavbarProps {
  systemStatus?: "ALERT" | "SECURE";
  alertCount?: number;
}

export default function Navbar({ systemStatus = "SECURE", alertCount = 0 }: NavbarProps) {
  const isAlert = systemStatus === "ALERT";

  return (
    <div
      className="h-16 w-full flex items-center justify-between px-6
      bg-slate-900/80 backdrop-blur border-b border-emerald-500/20"
    >
      <div className="flex items-center gap-3">
        <div className={`w-3 h-3 rounded-full animate-pulse ${isAlert ? "bg-red-400" : "bg-emerald-400"}`} />
        <h1 className="text-xl font-bold tracking-wide text-emerald-400">
          🌍 ECO RESCUE
        </h1>
        <span className="text-slate-400 text-sm">
          AI-Powered Disaster Management
        </span>
      </div>

      <div className="flex items-center gap-4">
        {isAlert && alertCount > 0 && (
          <span className="text-xs bg-red-500/20 border border-red-500/40 text-red-300 px-3 py-1 rounded-full font-medium">
            🚨 {alertCount} Active Alert{alertCount > 1 ? "s" : ""}
          </span>
        )}
        <span className="text-xs text-slate-400">
          System Status:{" "}
          <span className={`font-semibold ${isAlert ? "text-red-400" : "text-emerald-400"}`}>
            {systemStatus}
          </span>
        </span>
      </div>
    </div>
  );
}
