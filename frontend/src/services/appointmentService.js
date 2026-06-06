import apiClient from './apiClient';

export async function getAppointments() {
  const { data } = await apiClient.get('/api/appointments');
  return data;
}

export async function getAppointment(id) {
  const { data } = await apiClient.get(`/api/appointments/${id}`);
  return data;
}

export async function createAppointment(payload) {
  const aiEnabled = import.meta.env.VITE_AI_ENABLED === 'true';
  const { data } = await apiClient.post('/api/appointments', payload, {
    headers: { 'X-AI-Enabled': String(aiEnabled) },
  });
  return data;
}

export async function updateAppointmentStatus(id, status) {
  const { data } = await apiClient.patch(`/api/appointments/${id}/status`, { status });
  return data;
}

export async function deleteAppointment(id) {
  await apiClient.delete(`/api/appointments/${id}`);
}
