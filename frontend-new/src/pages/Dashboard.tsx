import { useEffect, useState } from "react";
import { getZones, getAlerts } from "../services/api";
import ZoneCard from "../components/ZoneCard";

export default function Dashboard() {
  const [zones, setZones] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);

  useEffect(() => {
    const load = async () => {
      setZones(await getZones());
      setAlerts(await getAlerts());
    };

    load();
    const i = setInterval(load, 2000);
    return () => clearInterval(i);
  }, []);

  const totals = {
    people: zones.reduce((a, z) => a + z.detected_people, 0),
    beds: zones.reduce((a, z) => a + z.available_beds, 0),
    zones: zones.length,
    status: alerts.length > 0 ? "ALERT" : "SECURE"
  };

  return (
    <div className="space-y-8">

      {/* ===== OVERVIEW ===== */}
      <section className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Stat title="People Detected" value={totals.people} />
        <Stat title="Beds Available" value={totals.beds} />
        <Stat title="Active Zones" value={totals.zones} />
        <Stat title="System Status" value={totals.status} accent />
      </section>

      {/* ===== ZONES ===== */}
      <section className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {zones.map(z => (
          <ZoneCard key={z.id} zone={z} />
        ))}

        {/* ===== ALERTS ===== */}
        <div className="rounded-xl border border-red-500/40 bg-red-500/10 p-6">
          <h3 className="text-xl font-bold text-red-400">
            🔥 Active Alerts
          </h3>

          <ul className="mt-3 space-y-2 text-sm">
            {alerts.length === 0 && (
              <li className="text-slate-400">
                No alerts currently
              </li>
            )}

            {alerts.map(a => (
              <li key={a.id} className="text-red-300">
                {a.zone_name}: {a.message}
              </li>
            ))}
          </ul>
        </div>
      </section>
    </div>
  );
}

function Stat({ title, value, accent = false }: any) {
  return (
    <div
      className={`rounded-xl p-6 border ${
        accent
          ? "border-red-400/40 bg-red-500/10"
          : "border-slate-700 bg-slate-900/70"
      }`}
    >
      <p className="text-sm uppercase text-slate-400">
        {title}
      </p>
      <p className="mt-2 text-4xl font-bold text-emerald-400">
        {value}
      </p>
    </div>
  );
}
