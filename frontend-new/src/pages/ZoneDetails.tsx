import { Link, useParams } from "react-router-dom";
import { useEffect, useState } from "react";
import RealTimeCharts from "../components/RealTimeCharts";
import { getZone } from "../services/api";

export default function ZoneDetails() {
  const { id } = useParams();
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    const load = async () => {
      const res = await getZone(Number(id));
      setData(res);
    };

    load();
    const interval = setInterval(load, 2000);
    return () => clearInterval(interval);
  }, [id]);

  if (!data) {
    return <div className="p-6 text-white">Loading...</div>;
  }

  return (
    <div className="w-full px-6 py-6 space-y-6">

      <Link to="/" className="text-cyan-400">
        ← Back
      </Link>

      <h1 className="text-3xl font-bold">
        {data.zone.name} — Live Zone Analysis
      </h1>

      {/* ===== FULL WIDTH CHARTS ===== */}
      <RealTimeCharts
        assignments={data.history}
        zone={data.zone}
      />

    </div>
  );
}
