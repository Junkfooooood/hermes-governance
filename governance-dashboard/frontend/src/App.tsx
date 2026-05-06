import { Navigate, Route, Routes } from "react-router-dom";
import Layout from "./components/Layout";
import OverviewPage from "./pages/OverviewPage";
import TaskListPage from "./pages/TaskListPage";
import TaskDetailPage from "./pages/TaskDetailPage";
import SubTaskDetailPage from "./pages/SubTaskDetailPage";
import AgentDetailPage from "./pages/AgentDetailPage";
import AlertCenterPage from "./pages/AlertCenterPage";
import AuditReplayPage from "./pages/AuditReplayPage";
import ConfigPage from "./pages/ConfigPage";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<OverviewPage />} />
        <Route path="/tasks" element={<TaskListPage />} />
        <Route path="/tasks/:txnId" element={<TaskDetailPage />} />
        <Route path="/tasks/:txnId/sub/:subId" element={<SubTaskDetailPage />} />
        <Route path="/agents" element={<AgentDetailPage />} />
        <Route path="/agents/:role" element={<AgentDetailPage />} />
        <Route path="/alerts" element={<AlertCenterPage />} />
        <Route path="/audit" element={<AuditReplayPage />} />
        <Route path="/config" element={<ConfigPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  );
}
