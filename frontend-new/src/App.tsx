import { Routes, Route } from "react-router-dom";
import { useEffect, useState } from "react";
import Navbar from "./components/Navbar";
import Dashboard from "./pages/Dashboard";
import ZoneDetails from "./pages/ZoneDetails";

export default function App() {
  const [alertCount, setAlertCount] = useState(0);

  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        const res = await fetch("http://localhost:8000/api/alerts");
        if (res.ok) {
          const data = await res.json();
          setAlertCount(Array.isArray(data) ? data.length : 0);
        }
      } catch {
        // backend not yet ready — ignore
      }
    };

    fetchAlerts();
    const interval = setInterval(fetchAlerts, 5000);
    return () => clearInterval(interval);
  }, []);

  const systemStatus: "ALERT" | "SECURE" = alertCount > 0 ? "ALERT" : "SECURE";

  return (
    <div className="min-h-screen bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-900 via-slate-950 to-black text-white">
      <Navbar systemStatus={systemStatus} alertCount={alertCount} />
      <main className="px-6 py-6">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/zone/:id" element={<ZoneDetails />} />
        </Routes>
      </main>
    </div>
  );
}
