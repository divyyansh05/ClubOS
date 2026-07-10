import { lazy, Suspense } from "react";
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
import UpcomingPage from "../features/upcoming/UpcomingPage";
import { AILayout } from "../features/ai/AILayout";

const AIChat = lazy(() => import("../features/ai/pages/AIChat"));
const AIAlerts = lazy(() => import("../features/ai/pages/AIAlerts"));
const AIAlertDetail = lazy(() => import("../features/ai/pages/AIAlertDetail"));
const AIInvestigations = lazy(() => import("../features/ai/pages/AIInvestigations"));
const AIInvestigationDetail = lazy(() => import("../features/ai/pages/AIInvestigationDetail"));
const AIBriefings = lazy(() => import("../features/ai/pages/AIBriefings"));
const AIBriefingDetail = lazy(() => import("../features/ai/pages/AIBriefingDetail"));

function AIPageLoader() {
  return (
    <div className="py-12 text-center font-mono text-sm uppercase tracking-wider text-stone-400 dark:text-stone-500">
      Loading…
    </div>
  );
}

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
        <Route path="/upcoming" element={<UpcomingPage />} />

        {/* AI section — additive, no v1 pages modified */}
        <Route path="/ai" element={<AILayout />}>
          <Route index element={<Navigate to="chat" replace />} />
          <Route path="chat" element={<Suspense fallback={<AIPageLoader />}><AIChat /></Suspense>} />
          <Route path="alerts" element={<Suspense fallback={<AIPageLoader />}><AIAlerts /></Suspense>} />
          <Route path="alerts/:alertId" element={<Suspense fallback={<AIPageLoader />}><AIAlertDetail /></Suspense>} />
          <Route path="investigations" element={<Suspense fallback={<AIPageLoader />}><AIInvestigations /></Suspense>} />
          <Route path="investigations/:investigationId" element={<Suspense fallback={<AIPageLoader />}><AIInvestigationDetail /></Suspense>} />
          <Route path="briefings" element={<Suspense fallback={<AIPageLoader />}><AIBriefings /></Suspense>} />
          <Route path="briefings/:briefingId" element={<Suspense fallback={<AIPageLoader />}><AIBriefingDetail /></Suspense>} />
        </Route>
      </Routes>
    </PageShell>
  );
}
