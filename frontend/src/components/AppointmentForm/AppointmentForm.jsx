import { useState } from 'react';
import toast from 'react-hot-toast';

const initialForm = {
  customer_name: '',
  phone_number: '',
  appointment_time: '',
  purpose: '',
};

function toLocalDateTimeValue(date) {
  const timezoneOffset = date.getTimezoneOffset() * 60000;
  return new Date(date.getTime() - timezoneOffset).toISOString().slice(0, 16);
}

export default function AppointmentForm({ onSubmit }) {
  const [form, setForm] = useState(initialForm);
  const [submitting, setSubmitting] = useState(false);

  const handleChange = ({ target: { name, value } }) => {
    setForm((current) => ({ ...current, [name]: value }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();
    setSubmitting(true);
    try {
      await onSubmit({
        ...form,
        appointment_time: new Date(form.appointment_time).toISOString(),
      });
      setForm(initialForm);
    } catch (error) {
      toast.error(error.message || 'Could not create appointment');
    } finally {
      setSubmitting(false);
    }
  };

  const inputClass =
    'mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm shadow-sm outline-none transition focus:border-blue-500 focus:ring-2 focus:ring-blue-200';

  return (
    <form onSubmit={handleSubmit} className="space-y-5 rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200 sm:p-8">
      <label className="block text-sm font-medium text-slate-700">
        Customer name
        <input
          name="customer_name"
          value={form.customer_name}
          onChange={handleChange}
          className={inputClass}
          autoComplete="name"
          maxLength={120}
          required
        />
      </label>

      <label className="block text-sm font-medium text-slate-700">
        Phone number
        <input
          name="phone_number"
          type="tel"
          value={form.phone_number}
          onChange={handleChange}
          placeholder="+15551234567"
          pattern="^\+[1-9]\d{7,14}$"
          className={inputClass}
          autoComplete="tel"
          required
        />
        <span className="mt-1 block text-xs text-slate-500">Use international E.164 format.</span>
      </label>

      <label className="block text-sm font-medium text-slate-700">
        Appointment time
        <input
          name="appointment_time"
          type="datetime-local"
          value={form.appointment_time}
          onChange={handleChange}
          min={toLocalDateTimeValue(new Date(Date.now() + 60000))}
          className={inputClass}
          required
        />
      </label>

      <label className="block text-sm font-medium text-slate-700">
        Purpose
        <textarea
          name="purpose"
          value={form.purpose}
          onChange={handleChange}
          rows={4}
          maxLength={1000}
          className={inputClass}
          required
        />
      </label>

      <button
        type="submit"
        disabled={submitting}
        className="w-full rounded-lg bg-blue-600 px-4 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {submitting ? 'Creating appointment...' : 'Create appointment'}
      </button>
    </form>
  );
}
