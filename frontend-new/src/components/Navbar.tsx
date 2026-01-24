export default function Navbar() {
  return (
    <div
      className="h-16 w-full flex items-center justify-between px-6
      bg-slate-900/80 backdrop-blur border-b border-emerald-500/20"
    >
      <div className="flex items-center gap-3">
        <div className="w-3 h-3 bg-emerald-400 rounded-full animate-pulse" />
        <h1 className="text-xl font-bold tracking-wide text-emerald-400">
          ECO RESCUE
        </h1>
        <span className="text-slate-400 text-sm">
          Live Monitoring Active
        </span>
      </div>

      <span className="text-xs text-slate-400">
        System Status:{" "}
        <span className="text-emerald-400 font-semibold">
          SECURE
        </span>
      </span>
    </div>
  );
}
