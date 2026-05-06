import { useCallback, useEffect, useState } from "react";
import { fetchJSON, postJSON } from "../lib/api";
import type { Alert } from "../lib/types";

interface UseAlertsParams {
  status?: string;
  severity?: string;
  since?: string;
}

interface UseAlertsResult {
  alerts: Alert[];
  loading: boolean;
  error: string | null;
  refresh: () => void;
  acknowledge: (alertId: string) => Promise<void>;
  suppress: (alertId: string, until: string) => Promise<void>;
}

export function useAlerts(params: UseAlertsParams = {}): UseAlertsResult {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const qs = new URLSearchParams();
      if (params.status) qs.set("status", params.status);
      if (params.severity) qs.set("severity", params.severity);
      if (params.since) qs.set("since", params.since);

      const data = await fetchJSON<{ alerts: Alert[] }>(
        `/api/alerts?${qs}`
      );
      setAlerts(data.alerts);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }, [params.status, params.severity, params.since]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const acknowledge = useCallback(
    async (alertId: string) => {
      await postJSON(`/api/alerts/${alertId}/ack`);
      await fetchData();
    },
    [fetchData]
  );

  const suppress = useCallback(
    async (alertId: string, until: string) => {
      await postJSON(`/api/alerts/${alertId}/suppress`, { until });
      await fetchData();
    },
    [fetchData]
  );

  return { alerts, loading, error, refresh: fetchData, acknowledge, suppress };
}
