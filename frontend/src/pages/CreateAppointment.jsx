import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import AppointmentForm from '../components/AppointmentForm/AppointmentForm';
import { createAppointment } from '../services/appointmentService';

export default function CreateAppointment() {
  const navigate = useNavigate();

  const handleCreate = async (formData) => {
    const appointment = await createAppointment(formData);
    toast.success(
      appointment.confirmation_sent || appointment.whatsapp_confirmation_sent
        ? 'Appointment created and confirmation sent'
        : 'Appointment created; messaging is pending',
    );
    navigate('/');
  };

  return (
    <section className="mx-auto max-w-2xl">
      <div className="mb-6">
        <p className="text-sm font-semibold uppercase tracking-wide text-blue-600">
          New booking
        </p>
        <h1 className="mt-1 text-3xl font-bold tracking-tight">Create Appointment</h1>
        <p className="mt-2 text-sm text-slate-500">
          Times are sent with your browser timezone and stored by the API in UTC.
        </p>
      </div>
      <AppointmentForm onSubmit={handleCreate} />
    </section>
  );
}
