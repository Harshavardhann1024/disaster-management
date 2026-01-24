import { useEffect, useState } from "react";

export default function YoloImagePanel() {
  const [images, setImages] = useState<any[]>([]);

  useEffect(() => {
    const load = async () => {
      const res = await fetch("http://localhost:8000/api/yolo-images");
      setImages(await res.json());
    };

    load();
    const i = setInterval(load, 5000);
    return () => clearInterval(i);
  }, []);

  return (
    <div className="col-span-1 xl:col-span-4 rounded-xl border border-white/10 bg-slate-900/60 p-6">
      <h3 className="text-lg font-semibold text-cyan-300 mb-4">
        📸 Live YOLO Detection (Zone-wise)
      </h3>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
        {images.map((img) => (
          <div
            key={img.zone_id}
            className="rounded-lg bg-black/40 border border-white/10 p-3"
          >
            <p className="text-sm mb-2 text-slate-300 font-medium">
              {img.zone_name} — 👥 {img.people_detected}
            </p>

            <img
              src={`data:image/jpeg;base64,${img.image}`}
              className="rounded-md w-full h-44 object-cover"
            />
          </div>
        ))}
      </div>
    </div>
  );
}
