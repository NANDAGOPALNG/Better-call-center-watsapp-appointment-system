import { useCallback, useEffect, useRef, useState } from 'react';
import { getDashboardAnalytics } from '../services/analyticsService';
import { getAppointments, updateAppointmentStatus } from '../services/appointmentService';

const emptyAnalytics = {
  total: 0,
  today: 0,
  confirmed: 0,
  pending: 0,
  reminder_sent: 0,
};

export default function useAppointments(refreshInterval = 5000) {
  const [appointments, setAppointments] = useState([]);
  const [analytics, setAnalytics] = useState(emptyAnalytics);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [updatingId, setUpdatingId] = useState(null);
  const mountedRef = useRef(true);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const [appointmentData, analyticsData] = await Promise.all([
        getAppointments(),
        getDashboardAnalytics(),
      ]);
      if (mountedRef.current) {
        setAppointments(appointmentData);
        setAnalytics(analyticsData);
        setError('');
      }
    } catch (requestError) {
      if (mountedRef.current) setError(requestError.message);
    } finally {
      if (mountedRef.current) setLoading(false);
    }
  }, []);

  const updateStatus = useCallback(async (id, status) => {
    setUpdatingId(id);
    try {
      const updated = await updateAppointmentStatus(id, status);
      setAppointments((current) =>
        current.map((appointment) => (appointment.id === id ? updated : appointment)),
      );
      const analyticsData = await getDashboardAnalytics();
      setAnalytics(analyticsData);
      return updated;
    } finally {
      setUpdatingId(null);
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    refresh();
    const intervalId = window.setInterval(refresh, refreshInterval);
    return () => {
      mountedRef.current = false;
      window.clearInterval(intervalId);
    };
  }, [refresh, refreshInterval]);

  return { appointments, analytics, loading, error, updatingId, refresh, updateStatus };
}
