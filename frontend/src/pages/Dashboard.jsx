import toast from 'react-hot-toast';
import AppointmentTable from '../components/AppointmentTable/AppointmentTable';
import DashboardCards from '../components/DashboardCards/DashboardCards';
import LoadingSpinner from '../components/LoadingSpinner/LoadingSpinner';
import useAppointments from '../hooks/useAppointments';

export default function Dashboard() {
  const {
    appointments,
    analytics,
    loading,
    error,
    updatingId,
    refresh,
    updateStatus,
  } = useAppointments();

  const handleStatusChange = async (appointmentId, status) => {
    try {
      await updateStatus(appointmentId, status);
      toast.success(`Status changed to ${status}`);
    } catch (requestError) {
      toast.error(requestError.message);
    }
  };

  if (loading && appointments.length === 0) {
    return <LoadingSpinner label="Loading dashboard..." />;
  }

  return (
    <section className="space-y-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-blue-600">
            Operations overview
          </p>
          <h1 className="mt-1 text-3xl font-bold tracking-tight">Appointment Dashboard</h1>
          <p className="mt-2 text-sm text-slate-500">
            Live appointment, confirmation, and reminder status.
          </p>
        </div>
        <button
          type="button"
          onClick={refresh}
          disabled={loading}
          className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-sm font-semibold shadow-sm transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? 'Refreshing...' : 'Refresh now'}
        </button>
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      <DashboardCards analytics={analytics} />
      <AppointmentTable
        appointments={appointments}
        updatingId={updatingId}
        onStatusChange={handleStatusChange}
      />
    </section>
  );
}
