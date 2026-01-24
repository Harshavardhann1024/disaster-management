export default function ShelterList({ shelters }: any) {
  return (
    <div className="rounded-xl border border-white/10 p-6">
      <h3 className="text-xl mb-4">Shelters</h3>

      {shelters.map((s: any, i: number) => {
        const ratio = s.available_beds / s.total_beds;
        const color =
          ratio < 0.2 ? "bg-red-500" :
          ratio < 0.5 ? "bg-yellow-400" :
          "bg-emerald-500";

        return (
          <div key={i} className="mb-3">
            <div className="flex justify-between text-sm">
              <span>{s.name}</span>
              <span>{s.available_beds}/{s.total_beds}</span>
            </div>
            <div className="h-2 bg-slate-700 rounded mt-1">
              <div className={`h-2 rounded ${color}`} style={{ width: `${ratio * 100}%` }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}
