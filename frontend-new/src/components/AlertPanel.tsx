export default function AlertPanel({ alerts }: any) {
  return (
    <div className="border border-red-500/30 rounded-lg p-4">
      <h3 className="text-red-400 mb-3">🔥 Alerts</h3>
      {alerts.map((a: any) => (
        <div key={a.id} className="mb-2 text-sm">
          <b>{a.zone_name}</b>: {a.title}
        </div>
      ))}
    </div>
  );
}
