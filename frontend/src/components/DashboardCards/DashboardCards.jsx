const cards = [
  { key: 'total', label: 'Total', accent: 'text-slate-900' },
  { key: 'today', label: 'Today', accent: 'text-cyan-700' },
  { key: 'confirmed', label: 'Confirmed', accent: 'text-blue-700' },
  { key: 'pending', label: 'Pending', accent: 'text-amber-700' },
  { key: 'reminder_sent', label: 'Reminders sent', accent: 'text-violet-700' },
];

export default function DashboardCards({ analytics }) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
      {cards.map(({ key, label, accent }) => (
        <article key={key} className="rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200">
          <p className="text-sm font-medium text-slate-500">{label}</p>
          <p className={`mt-2 text-3xl font-bold ${accent}`}>{analytics[key] ?? 0}</p>
        </article>
      ))}
    </div>
  );
}
