interface StateWrapperProps {
  loading: boolean;
  error: string | null;
  empty: boolean;
  emptyMessage?: string;
  onRetry?: () => void;
  children: React.ReactNode;
}

export default function StateWrapper({
  loading,
  error,
  empty,
  emptyMessage = "暂无数据",
  onRetry,
  children,
}: StateWrapperProps) {
  if (loading) {
    return (
      <div className="space-y-3">
        <div className="animate-pulse h-8 bg-gray-100 rounded w-48" />
        <div className="animate-pulse h-32 bg-gray-100 rounded" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="border border-red-200 bg-red-50 rounded-lg p-4">
        <p className="text-sm text-red-600">{error}</p>
        {onRetry && (
          <button
            onClick={onRetry}
            className="mt-2 text-sm text-red-700 underline hover:text-red-900"
          >
            重试
          </button>
        )}
      </div>
    );
  }

  if (empty) {
    return (
      <div className="border border-gray-200 bg-gray-50 rounded-lg p-8 text-center">
        <p className="text-sm text-gray-400">{emptyMessage}</p>
      </div>
    );
  }

  return <>{children}</>;
}
