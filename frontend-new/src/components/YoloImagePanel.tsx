import { useEffect, useState } from "react";

export default function YoloImagePanel() {
  const [data, setData] = useState<any[]>([]);

  useEffect(() => {
    const load = async () => {
      const res = await fetch("http://localhost:8000/api/yolo-images");
      setData(await res.json());
    };
    load();
    const i = setInterval(load, 10000);
    return () => clearInterval(i);
  }, []);

  return (
    <div className="border border-cyan-400/30 rounded-xl p-4 bg-slate-900/60">
      <h3 className="text-cyan-300 mb-4">📷 Live YOLO Detection</h3>

      <div className="grid grid-cols-2 gap-4">
        {data.map(d => (
          <div key={d.zone_id}>
            <p className="text-sm mb-1">
              {d.zone_name} — 👥 {d.people}
            </p>
            <img
              src={`data:image/jpeg;base64,${d.image}`}
              className="rounded-lg border border-white/10"
            />
          </div>
        ))}
      </div>
    </div>
  );
}
