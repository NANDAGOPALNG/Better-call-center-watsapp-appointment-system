import apiClient from './apiClient';

export async function getDashboardAnalytics() {
  const { data } = await apiClient.get('/api/analytics/dashboard');
  return data;
}
