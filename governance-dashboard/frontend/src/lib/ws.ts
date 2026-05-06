import type { GovernanceEvent } from "./types";

type Listener = (event: GovernanceEvent) => void;

class GovernanceWebSocket {
  private ws: WebSocket | null = null;
  private lastGlobalSeq = 0;
  private seenEventIds = new Set<string>();
  private maxSeenIds = 10000;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private reconnectDelay = 1000;
  private maxReconnectDelay = 30000;
  private listeners: Set<Listener> = new Set();
  private _connected = false;
  private connectionListeners: Set<(connected: boolean) => void> = new Set();

  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) return;

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws/events`;

    try {
      this.ws = new WebSocket(wsUrl);
    } catch {
      this._scheduleReconnect();
      return;
    }

    this.ws.onopen = () => {
      this._connected = true;
      this.reconnectDelay = 1000;
      this.connectionListeners.forEach((fn) => fn(true));
      this.ws!.send(
        JSON.stringify({
          type: "subscribe",
          last_global_seq: this.lastGlobalSeq,
        })
      );
    };

    this.ws.onmessage = (msg) => {
      try {
        const event: GovernanceEvent = JSON.parse(msg.data);
        // Dedup by event_id
        if (this.seenEventIds.has(event.event_id)) return;
        this.seenEventIds.add(event.event_id);
        // Evict oldest if over limit
        if (this.seenEventIds.size > this.maxSeenIds) {
          const iter = this.seenEventIds.values();
          for (let i = 0; i < 1000; i++) {
            const next = iter.next();
            if (next.done) break;
            this.seenEventIds.delete(next.value);
          }
        }
        this.lastGlobalSeq = Math.max(this.lastGlobalSeq, event.global_seq);
        this.listeners.forEach((fn) => fn(event));
      } catch {
        // Ignore malformed messages
      }
    };

    this.ws.onclose = () => {
      this._connected = false;
      this.connectionListeners.forEach((fn) => fn(false));
      this._scheduleReconnect();
    };

    this.ws.onerror = () => {
      this.ws?.close();
    };
  }

  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    this.ws?.close();
    this.ws = null;
    this._connected = false;
    this.connectionListeners.forEach((fn) => fn(false));
  }

  subscribe(listener: Listener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  onConnectionChange(listener: (connected: boolean) => void): () => void {
    this.connectionListeners.add(listener);
    return () => this.connectionListeners.delete(listener);
  }

  isConnected(): boolean {
    return this._connected;
  }

  private _scheduleReconnect(): void {
    if (this.reconnectTimer) return;
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, this.reconnectDelay);
    this.reconnectDelay = Math.min(
      this.reconnectDelay * 2,
      this.maxReconnectDelay
    );
  }
}

// Singleton
let instance: GovernanceWebSocket | null = null;

export function getWebSocket(): GovernanceWebSocket {
  if (!instance) {
    instance = new GovernanceWebSocket();
  }
  return instance;
}
