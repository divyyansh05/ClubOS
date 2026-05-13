import { Routes, Route, Navigate } from "react-router-dom";
import { PageShell } from "../components/ui/PageShell";
import { PriorityBoardPage } from "../features/priority-board/PriorityBoardPage";
import { CommandCenterPage } from "../features/command-center/CommandCenterPage";
import { PeerBenchmarkPage } from "../features/peer-benchmark/PeerBenchmarkPage";
import { SignalEnginePage } from "../features/signal-engine/SignalEnginePage";
import { MonthlyBriefingPage } from "../features/monthly-briefing/MonthlyBriefingPage";

export default function App() {
  return (
    <PageShell>
      <Routes>
        <Route path="/" element={<Navigate to="/priorities" replace />} />
        <Route path="/priorities" element={<PriorityBoardPage />} />
        <Route path="/command-center" element={<CommandCenterPage />} />
        <Route path="/benchmark" element={<PeerBenchmarkPage />} />
        <Route path="/signals" element={<SignalEnginePage />} />
        <Route path="/briefing" element={<MonthlyBriefingPage />} />
      </Routes>
    </PageShell>
  );
}
