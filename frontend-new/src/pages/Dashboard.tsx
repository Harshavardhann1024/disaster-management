import { useEffect, useState } from "react";
import { getZones, getAlerts } from "../services/api";
import ZoneCard from "../components/ZoneCard";
import YoloImagePanel from "../components/YoloImagePanel";

export default function Dashboard() {
  const [zones, setZones] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);

  useEffect(() => {
    const load = async () => {
      try {
        const z = await getZones();
        const a = await getAlerts();
        setZones(z);
        setAlerts(a);
      } catch (err) {
        console.error("Dashboard fetch error", err);
      }
    };

    load();
    const interval = setInterval(load, 5000); // realtime refresh
    return () => clearInterval(interval);
  }, []);

  // ---- OVERALL STATS ----
  const totalPeople = zones.reduce(
    (sum, z) => sum + (z.detected_people || 0),
    0
  );

  const totalBeds = zones.reduce(
    (sum, z) => sum + (z.available_beds || 0),
    0
  );

  return (
    <div className="space-y-8">

      {/* ================= TOP STATS ================= */}
      <section className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Stat title="People Detected" value={totalPeople} />
        <Stat title="Beds Available" value={totalBeds} />
        <Stat title="Active Zones" value={zones.length} />
        <Stat
          title="System Status"
          value={alerts.length > 0 ? "ALERT" : "SECURE"}
          accent
        />
      </section>

      {/* ================= ZONES + YOLO ================= */}
      <section className="grid grid-cols-1 xl:grid-cols-4 gap-6">
        {/* ZONE CARDS */}
        {zones.map((z) => (
          <ZoneCard key={z.id} zone={z} />
        ))}

        {/* YOLO PANEL */}
        <YoloImagePanel />
      </section>

      {/* ================= ALERTS ================= */}
      <section className="rounded-xl border border-red-500/40 bg-red-500/10 p-6">
        <h3 className="text-xl font-bold text-red-400">🔥 Alerts</h3>

        {alerts.length === 0 ? (
          <p className="mt-3 text-sm text-slate-400">
            No active alerts
          </p>
        ) : (
          <ul className="mt-3 space-y-2 text-sm">
            {alerts.map((a) => (
              <li key={a.id} className="text-red-300">
                <b>{a.zone_name}</b>: {a.message}
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}

/* ================= SMALL STAT CARD ================= */

function Stat({
  title,
  value,
  accent = false,
}: {
  title: string;
  value: any;
  accent?: boolean;
}) {
  return (
    <div
      className={`rounded-xl p-6 border ${
        accent
          ? "border-red-400/40 bg-red-500/10"
          : "border-slate-700 bg-slate-900/70"
      }`}
    >
      <p className="text-sm uppercase text-slate-400">{title}</p>
      <p className="mt-2 text-4xl font-bold text-emerald-400">
        {value}
      </p>
    </div>
  );
}
