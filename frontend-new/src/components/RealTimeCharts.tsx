import {
  LineChart, Line, XAxis, YAxis, Tooltip,
  BarChart, Bar, ResponsiveContainer
} from "recharts";

export default function RealTimeCharts({ history }: any) {

  const data = history.map((h: any) => ({
    ...h,
    time: new Date(h.created_at).toLocaleTimeString()
  }));

  return (
    <div className="space-y-10 w-full">

      <div className="border border-white/10 rounded-xl p-6 bg-slate-900/60">
        <h3 className="text-lg text-cyan-300 mb-4">
          Beds Allocation Over Time
        </h3>

        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data}>
            <XAxis dataKey="time" />
            <YAxis />
            <Tooltip />
            <Line
              dataKey="beds_allocated"
              stroke="#22d3ee"
              strokeWidth={3}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="border border-white/10 rounded-xl p-6 bg-slate-900/60">
        <h3 className="text-lg text-purple-300 mb-4">
          Volunteers Assigned Over Time
        </h3>

        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data}>
            <XAxis dataKey="time" />
            <YAxis />
            <Tooltip />
            <Bar dataKey="volunteers_assigned" fill="#a855f7" />
          </BarChart>
        </ResponsiveContainer>
      </div>

    </div>
  );
}
