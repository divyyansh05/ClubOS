import { Routes, Route, Navigate } from "react-router-dom";
import { PageShell } from "../components/ui/PageShell";
import { PriorityBoardPage } from "../features/priority-board/PriorityBoardPage";
import { CommandCenterPage } from "../features/command-center/CommandCenterPage";
import { PeerBenchmarkPage } from "../features/peer-benchmark/PeerBenchmarkPage";
import { SignalEnginePage } from "../features/signal-engine/SignalEnginePage";
import EventCalendarPage from "../features/events/EventCalendarPage";
import { MonthlyBriefingPage } from "../features/monthly-briefing/MonthlyBriefingPage";
import SocialIntelligencePage from "../features/social/SocialIntelligencePage";
import ConnectorsPage from "../features/connectors/ConnectorsPage";

export default function App() {
  return (
    <PageShell>
      <Routes>
        <Route path="/" element={<Navigate to="/priorities" replace />} />
        <Route path="/priorities" element={<PriorityBoardPage />} />
        <Route path="/command-center" element={<CommandCenterPage />} />
        <Route path="/benchmark" element={<PeerBenchmarkPage />} />
        <Route path="/signals" element={<SignalEnginePage />} />
        <Route path="/events" element={<EventCalendarPage />} />
        <Route path="/social" element={<SocialIntelligencePage />} />
        <Route path="/connectors" element={<ConnectorsPage />} />
        <Route path="/briefing" element={<MonthlyBriefingPage />} />
      </Routes>
    </PageShell>
  );
}
