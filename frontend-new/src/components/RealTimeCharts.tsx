import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  BarChart,
  Bar,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";

const COLORS = ["#ef4444", "#22c55e"];

export default function RealTimeCharts({
  assignments,
  zone,
}: {
  assignments: any[];
  zone: any;
}) {
  const data = assignments.map((a: any) => ({
    ...a,
    time: new Date(a.created_at).toLocaleTimeString(),
  }));

  const capacityData = [
    { name: "Beds Used", value: zone.total_beds - zone.available_beds },
    { name: "Beds Available", value: zone.available_beds },
  ];

  return (
    <div className="grid grid-cols-1 xl:grid-cols-2 gap-6 w-full">

      {/* ===== BEDS LINE CHART ===== */}
      <div className="border border-white/10 rounded-xl p-4 bg-slate-900/60">
        <h3 className="text-sm font-semibold text-cyan-300 mb-2">
          Beds Allocation Over Time
        </h3>

        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={data}>
            <XAxis dataKey="time" tick={{ fontSize: 10 }} />
            <YAxis allowDecimals={false} />
            <Tooltip />
            <Line
              dataKey="beds_allocated"
              stroke="#22d3ee"
              strokeWidth={2}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* ===== VOLUNTEERS BAR CHART ===== */}
      <div className="border border-white/10 rounded-xl p-4 bg-slate-900/60">
        <h3 className="text-sm font-semibold text-purple-300 mb-2">
          Volunteers Assigned Over Time
        </h3>

        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={data}>
            <XAxis dataKey="time" tick={{ fontSize: 10 }} />
            <YAxis allowDecimals={false} />
            <Tooltip />
            <Bar dataKey="volunteers_assigned" fill="#a855f7" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* ===== CAPACITY PIE (FULL WIDTH) ===== */}
      <div className="border border-white/10 rounded-xl p-4 bg-slate-900/60 xl:col-span-2">
        <h3 className="text-sm font-semibold text-emerald-300 mb-2">
          Shelter Capacity Distribution
        </h3>

        <ResponsiveContainer width="100%" height={220}>
          <PieChart>
            <Pie
              data={capacityData}
              dataKey="value"
              outerRadius={80}
              label
            >
              {capacityData.map((_, i) => (
                <Cell key={i} fill={COLORS[i]} />
              ))}
            </Pie>
            <Legend />
          </PieChart>
        </ResponsiveContainer>
      </div>

    </div>
  );
}
