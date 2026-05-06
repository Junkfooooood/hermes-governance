import { useCallback, useEffect, useState } from "react";
import { fetchJSON } from "../lib/api";
import type { TaskSummary } from "../lib/types";

interface UseTasksParams {
  state?: string;
  search?: string;
  sort?: string;
  limit?: number;
  offset?: number;
}

interface UseTasksResult {
  tasks: TaskSummary[];
  total: number;
  loading: boolean;
  error: string | null;
  refresh: () => void;
}

export function useTasks(params: UseTasksParams = {}): UseTasksResult {
  const [tasks, setTasks] = useState<TaskSummary[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const qs = new URLSearchParams();
      if (params.state) qs.set("state", params.state);
      if (params.search) qs.set("search", params.search);
      if (params.sort) qs.set("sort", params.sort);
      if (params.limit) qs.set("limit", String(params.limit));
      if (params.offset) qs.set("offset", String(params.offset));

      const data = await fetchJSON<{
        tasks: TaskSummary[];
        total: number;
      }>(`/api/tasks?${qs}`);
      setTasks(data.tasks);
      setTotal(data.total);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  }, [params.state, params.search, params.sort, params.limit, params.offset]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  return { tasks, total, loading, error, refresh: fetchData };
}
