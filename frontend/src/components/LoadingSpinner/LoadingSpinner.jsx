export default function LoadingSpinner({ label = 'Loading...' }) {
  return (
    <div className="flex min-h-64 flex-col items-center justify-center gap-3" role="status">
      <div className="h-10 w-10 animate-spin rounded-full border-4 border-blue-200 border-t-blue-600" />
      <span className="text-sm font-medium text-slate-600">{label}</span>
    </div>
  );
}
