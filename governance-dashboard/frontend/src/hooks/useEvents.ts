import { useEffect, useState } from "react";
import { getWebSocket } from "../lib/ws";
import type { GovernanceEvent } from "../lib/types";

interface UseEventsFilter {
  txn_id?: string;
  type?: string;
}

interface UseEventsResult {
  events: GovernanceEvent[];
  connected: boolean;
}

/**
 * Hook for subscribing to real-time governance events.
 * Optional filter by txn_id and/or event type.
 */
export function useEvents(filter?: UseEventsFilter): UseEventsResult {
  const [events, setEvents] = useState<GovernanceEvent[]>([]);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    const ws = getWebSocket();
    ws.connect();

    const unsubEvent = ws.subscribe((event) => {
      if (filter?.txn_id && event.txn_id !== filter.txn_id) return;
      if (filter?.type && event.type !== filter.type) return;
      setEvents((prev) => [...prev, event]);
    });

    const unsubConn = ws.onConnectionChange(setConnected);
    setConnected(ws.isConnected());

    return () => {
      unsubEvent();
      unsubConn();
    };
  }, [filter?.txn_id, filter?.type]);

  return { events, connected };
}
