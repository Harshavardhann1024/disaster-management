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
    <div className="space-y-10 w-full">

      {/* Beds */}
      <div className="border border-white/10 rounded-xl p-6 bg-slate-900/60">
        <h3 className="text-lg font-semibold text-cyan-300 mb-4">
          Beds Allocation Over Time
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data}>
            <XAxis dataKey="time" />
            <YAxis allowDecimals={false} />
            <Tooltip />
            <Line dataKey="beds_allocated" stroke="#22d3ee" strokeWidth={3} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Volunteers */}
      <div className="border border-white/10 rounded-xl p-6 bg-slate-900/60">
        <h3 className="text-lg font-semibold text-purple-300 mb-4">
          Volunteers Assigned Over Time
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data}>
            <XAxis dataKey="time" />
            <YAxis allowDecimals={false} />
            <Tooltip />
            <Bar dataKey="volunteers_assigned" fill="#a855f7" />
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Capacity */}
      <div className="border border-white/10 rounded-xl p-6 bg-slate-900/60">
        <h3 className="text-lg font-semibold text-emerald-300 mb-4">
          Shelter Capacity Distribution
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie data={capacityData} outerRadius={90} dataKey="value" label>
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
