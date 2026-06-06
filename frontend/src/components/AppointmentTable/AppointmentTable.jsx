const STATUSES = ['Scheduled', 'Confirmed', 'Reminder Sent', 'Completed', 'Cancelled'];

const statusStyles = {
  Scheduled: 'bg-amber-50 text-amber-700 ring-amber-600/20',
  Confirmed: 'bg-blue-50 text-blue-700 ring-blue-600/20',
  'Reminder Sent': 'bg-violet-50 text-violet-700 ring-violet-600/20',
  Completed: 'bg-emerald-50 text-emerald-700 ring-emerald-600/20',
  Cancelled: 'bg-red-50 text-red-700 ring-red-600/20',
};

function StatusBadge({ status }) {
  return (
    <span className={`inline-flex rounded-full px-2 py-1 text-xs font-medium ring-1 ring-inset ${statusStyles[status] || 'bg-slate-100 text-slate-700 ring-slate-500/20'}`}>
      {status}
    </span>
  );
}

export default function AppointmentTable({ appointments, updatingId, onStatusChange }) {
  if (appointments.length === 0) {
    return (
      <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-12 text-center">
        <h2 className="font-semibold text-slate-900">No appointments yet</h2>
        <p className="mt-1 text-sm text-slate-500">Create the first appointment to populate the dashboard.</p>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-2xl bg-white shadow-sm ring-1 ring-slate-200">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
          <thead className="bg-slate-50 text-xs font-semibold uppercase tracking-wide text-slate-500">
            <tr>
              <th className="px-4 py-3">Customer</th>
              <th className="px-4 py-3">Phone</th>
              <th className="px-4 py-3">Appointment</th>
              <th className="px-4 py-3">Purpose</th>
              <th className="px-4 py-3">AI Summary</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Delivery</th>
              <th className="px-4 py-3">Update</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {appointments.map((appointment) => (
              <tr key={appointment.id} className="align-top hover:bg-slate-50/70">
                <td className="whitespace-nowrap px-4 py-4 font-medium text-slate-900">{appointment.customer_name}</td>
                <td className="whitespace-nowrap px-4 py-4 text-slate-600">{appointment.phone_number}</td>
                <td className="whitespace-nowrap px-4 py-4 text-slate-600">
                  {new Intl.DateTimeFormat(undefined, { dateStyle: 'medium', timeStyle: 'short' }).format(new Date(appointment.appointment_time))}
                </td>
                <td className="max-w-xs px-4 py-4 text-slate-600">{appointment.purpose}</td>
                <td className="max-w-sm px-4 py-4 text-slate-600">{appointment.ai_summary || 'Not available'}</td>
                <td className="whitespace-nowrap px-4 py-4"><StatusBadge status={appointment.status} /></td>
                <td className="whitespace-nowrap px-4 py-4 text-xs text-slate-600">
                  <div>SMS/Mock: {appointment.confirmation_sent ? 'Confirmed' : 'Pending'}</div>
                  <div>WhatsApp: {appointment.whatsapp_confirmation_sent ? 'Confirmed' : 'Pending'}</div>
                  <div>Reminder: {(appointment.reminder_sent || appointment.whatsapp_reminder_sent) ? 'Sent' : 'Pending'}</div>
                </td>
                <td className="whitespace-nowrap px-4 py-4">
                  <select
                    value={appointment.status}
                    onChange={(event) => onStatusChange(appointment.id, event.target.value)}
                    disabled={updatingId === appointment.id}
                    aria-label={`Update status for ${appointment.customer_name}`}
                    className="rounded-md border border-slate-300 bg-white px-2 py-1.5 text-sm outline-none focus:border-blue-500 focus:ring-2 focus:ring-blue-200 disabled:opacity-60"
                  >
                    {STATUSES.map((status) => <option key={status}>{status}</option>)}
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
