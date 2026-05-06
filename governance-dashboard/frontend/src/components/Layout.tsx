import { useEffect, useState } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { fetchJSON } from "../lib/api";

const NAV_ITEMS = [
  { path: "/", label: "总览", icon: " " },
  { path: "/tasks", label: "任务看板", icon: " " },
  { path: "/agents", label: "Agent", icon: " " },
  { path: "/alerts", label: "告警中心", icon: " " },
  { path: "/audit", label: "审计回放", icon: " " },
  { path: "/config", label: "配置", icon: " " },
];

export default function Layout() {
  const [wsConnected, setWsConnected] = useState(false);
  const [activeCount, setActiveCount] = useState(0);
  const [lastEventTime, setLastEventTime] = useState<string | null>(null);

  // Fetch active count periodically
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await fetchJSON<{
          active_count: number;
        }>("/api/overview");
        setActiveCount(data.active_count);
      } catch {
        // silent
      }
    };
    fetchStats();
    const interval = setInterval(fetchStats, 15000);
    return () => clearInterval(interval);
  }, []);

  // WebSocket connection
  useEffect(() => {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws/events`;
    let ws: WebSocket;
    let reconnectTimer: ReturnType<typeof setTimeout>;
    let disposed = false;

    const connect = () => {
      if (disposed) return;
      ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        setWsConnected(true);
        // Send reconnect seq
        ws.send(JSON.stringify({ last_global_seq: 0 }));
      };

      ws.onmessage = () => {
        setLastEventTime(
          new Date().toLocaleTimeString("zh-CN", {
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
          })
        );
      };

      ws.onclose = () => {
        setWsConnected(false);
        if (!disposed) {
          reconnectTimer = setTimeout(connect, 3000);
        }
      };

      ws.onerror = () => {
        ws.close();
      };
    };

    connect();

    return () => {
      disposed = true;
      clearTimeout(reconnectTimer);
      ws?.close();
    };
  }, []);

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-56 bg-white border-r border-gray-200 flex flex-col shrink-0">
        <div className="px-4 py-5 border-b border-gray-100">
          <h1 className="text-base font-semibold text-gray-900 tracking-tight">
            Governance Dashboard
          </h1>
          <p className="text-xs text-gray-400 mt-0.5">三省六部监控平台</p>
        </div>
        <nav className="flex-1 px-2 py-3 space-y-0.5">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === "/"}
              className={({ isActive }) =>
                `flex items-center gap-2.5 px-3 py-2 text-sm rounded-md transition-colors ${
                  isActive
                    ? "bg-gray-100 text-gray-900 font-medium"
                    : "text-gray-500 hover:text-gray-700 hover:bg-gray-50"
                }`
              }
            >
              <span className="text-base">{item.icon}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top status bar — monitoring feel */}
        <header className="h-10 bg-white border-b border-gray-200 flex items-center px-4 gap-5 shrink-0">
          {/* Connection indicator */}
          <div className="flex items-center gap-1.5">
            <span
              className={`w-2 h-2 rounded-full transition-colors ${
                wsConnected
                  ? "bg-green-500 shadow-[0_0_6px_rgba(34,197,94,0.4)]"
                  : "bg-red-400"
              }`}
            />
            <span className="text-xs text-gray-500">
              {wsConnected ? "实时连接" : "未连接"}
            </span>
          </div>

          {/* Separator */}
          <div className="w-px h-4 bg-gray-200" />

          {/* Active tasks */}
          <div className="flex items-center gap-1.5 text-xs text-gray-500">
            <span>活跃任务</span>
            <span
              className={`font-semibold ${
                activeCount > 0 ? "text-blue-600" : "text-gray-400"
              }`}
            >
              {activeCount}
            </span>
            {activeCount > 0 && (
              <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
            )}
          </div>

          {/* Separator */}
          <div className="w-px h-4 bg-gray-200" />

          {/* Last event */}
          <div className="text-xs text-gray-400">
            {lastEventTime
              ? `最近事件: ${lastEventTime}`
              : "等待事件..."}
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-auto p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
