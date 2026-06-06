import apiClient from './apiClient';

export async function getHealth() {
  const { data } = await apiClient.get('/api/health');
  return data;
}
