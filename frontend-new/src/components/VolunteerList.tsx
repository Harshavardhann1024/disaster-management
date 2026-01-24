export default function VolunteerList({ assigned, available }: any) {
  return (
    <div className="space-y-4">
      <Section title="Assigned Volunteers" color="emerald">
        {assigned.map((v: any) => (
          <Item key={v.name} label={v.name} status="Assigned" />
        ))}
      </Section>

      <Section title="Available Volunteers" color="cyan">
        {available.map((v: any) => (
          <Item key={v.name} label={v.name} status="Available" />
        ))}
      </Section>
    </div>
  );
}

function Section({ title, children, color }: any) {
  return (
    <div>
      <h3 className={`text-${color}-400 font-semibold mb-2`}>
        {title}
      </h3>
      <div className="space-y-2">{children}</div>
    </div>
  );
}

function Item({ label, status }: any) {
  return (
    <div className="flex justify-between p-3 rounded-lg border border-white/10 bg-slate-900/40">
      <span>{label}</span>
      <span className="text-sm text-slate-400">{status}</span>
    </div>
  );
}
