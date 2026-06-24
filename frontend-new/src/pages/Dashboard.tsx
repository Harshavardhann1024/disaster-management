import { useEffect, useState } from "react";
import { getZones, getAlerts, getMedicalAlerts } from "../services/api";
import ZoneCard from "../components/ZoneCard";
import YoloImagePanel from "../components/YoloImagePanel";
import PredictionsPanel from "../components/PredictionsPanel";
import MedicalAlertsPanel from "../components/MedicalAlertsPanel";
import AlertPanel from "../components/AlertPanel";

export default function Dashboard() {
  const [zones, setZones] = useState<any[]>([]);
  const [alerts, setAlerts] = useState<any[]>([]);
  const [medicalAlerts, setMedicalAlerts] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        setError(null);
        const z = await getZones();
        const a = await getAlerts();
        const m = await getMedicalAlerts();
        setZones(z || []);
        setAlerts(a || []);
        setMedicalAlerts(m || []);
        setIsLoading(false);
      } catch (err) {
        console.error("Dashboard fetch error", err);
        setError("Failed to load dashboard data");
        setIsLoading(false);
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

  const systemStatus = alerts.length > 0 ? "ALERT" : "SECURE";

  return (
    <div className="space-y-8">
      {isLoading && (
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
            <p className="mt-4 text-slate-400">Loading EcoRescue dashboard...</p>
          </div>
        </div>
      )}

      {error && (
        <div className="rounded-xl border border-red-500/40 bg-red-500/10 p-6 text-red-400">
          <p>⚠️ {error}</p>
          <p className="text-sm mt-2">Make sure the backend is running on http://localhost:8000</p>
        </div>
      )}

      {!isLoading && !error && (
        <>
          {/* ================= TOP STATS BAR ================= */}
          <section className="grid grid-cols-1 md:grid-cols-4 gap-6">
            <Stat title="People Detected" value={totalPeople} />
            <Stat title="Beds Available" value={totalBeds} />
            <Stat title="Active Zones" value={zones.length} />
            <Stat
              title="System Status"
              value={systemStatus}
              accent={systemStatus === "ALERT"}
            />
          </section>

          {/* ================= ZONE CARDS ================= */}
          <section>
            <h2 className="text-lg font-semibold text-slate-300 mb-4">📍 Zone Monitoring</h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-6">
              {zones.map((z) => (
                <ZoneCard key={z.id} zone={z} />
              ))}
            </div>
          </section>

          {/* ================= YOLO PANEL ================= */}
          <section>
            <YoloImagePanel />
          </section>

          {/* ================= MEDICAL ALERTS ================= */}
          <section>
            <MedicalAlertsPanel alerts={medicalAlerts} />
          </section>

          {/* ================= LSTM PREDICTIONS ================= */}
          <section>
            <PredictionsPanel zones={zones} />
          </section>

          {/* ================= ALERTS PANEL ================= */}
          <section>
            <AlertPanel alerts={alerts} />
          </section>
        </>
      )}
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
      className={`rounded-xl p-6 border ${accent
          ? "border-red-400/40 bg-red-500/10"
          : "border-slate-700 bg-slate-900/70"
        }`}
    >
      <p className="text-sm uppercase text-slate-400">{title}</p>
      <p className={`mt-2 text-4xl font-bold ${accent ? "text-red-400" : "text-emerald-400"}`}>
        {value}
      </p>
    </div>
  );
}
