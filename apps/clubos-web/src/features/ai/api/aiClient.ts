import { AI_ENDPOINTS } from './endpoints';
import type {
  SupervisorRequest,
  SupervisorResponse,
  WatchdogAlertRead,
  WatchdogRunRequest,
  WatchdogRunResponse,
  AlertsListResponse,
  AcknowledgeResponse,
  InvestigateRequest,
  InvestigateResponse,
  InvestigationListResponse,
  InvestigationRead,
  BriefingRunResult,
  BriefingRead,
} from './types';

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? '';

async function get<TResp>(path: string): Promise<TResp> {
  const response = await fetch(`${API_BASE}${path}`);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`GET ${path} failed: ${response.status} ${text}`);
  }
  return response.json() as Promise<TResp>;
}

async function post<TReq, TResp>(path: string, body?: TReq): Promise<TResp> {
  const response = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: body !== undefined ? JSON.stringify(body) : undefined,
  });
  if (!response.ok) {
    const text = await response.text();
    throw new Error(`POST ${path} failed: ${response.status} ${text}`);
  }
  return response.json() as Promise<TResp>;
}

function buildQuery(params: Record<string, unknown>): string {
  const entries = Object.entries(params).filter(([, v]) => v !== undefined && v !== null);
  if (entries.length === 0) return '';
  return '?' + new URLSearchParams(entries.map(([k, v]) => [k, String(v)])).toString();
}

export const aiClient = {
  supervisor: {
    query: (req: SupervisorRequest): Promise<SupervisorResponse> =>
      post(AI_ENDPOINTS.supervisor.query, req),
  },

  watchdog: {
    run: (req: WatchdogRunRequest = {}): Promise<WatchdogRunResponse> =>
      post(AI_ENDPOINTS.watchdog.run, req),

    listAlerts: (params: {
      limit?: number;
      since_hours?: number;
      metric_name?: string;
      severity?: string;
      run_id?: string;
      unacknowledged_only?: boolean;
    } = {}): Promise<AlertsListResponse> =>
      get(AI_ENDPOINTS.watchdog.alerts + buildQuery(params)),

    // No dedicated GET /alerts/{id} endpoint — fetch list and find by ID
    getAlertById: async (alertId: string): Promise<WatchdogAlertRead | null> => {
      const resp = await get<AlertsListResponse>(AI_ENDPOINTS.watchdog.alerts + '?limit=200');
      return resp.alerts.find((a) => a.alert_id === alertId) ?? null;
    },

    acknowledgeAlert: (alertId: string, acknowledgedBy: string): Promise<AcknowledgeResponse> =>
      post(AI_ENDPOINTS.watchdog.acknowledge(alertId), { acknowledged_by: acknowledgedBy }),
  },

  investigator: {
    run: (alertId: string, req: InvestigateRequest = {}): Promise<InvestigateResponse> =>
      post(AI_ENDPOINTS.investigator.run(alertId), req),

    list: (params: {
      limit?: number;
      metric_name?: string;
      status?: string;
      alert_id?: string;
    } = {}): Promise<InvestigationListResponse> =>
      get(AI_ENDPOINTS.investigator.list + buildQuery(params)),

    getById: (id: string): Promise<InvestigationRead> =>
      get(AI_ENDPOINTS.investigator.getById(id)),
  },

  briefer: {
    runMonthly: (yearMonth?: string): Promise<BriefingRunResult> =>
      post(AI_ENDPOINTS.briefer.runMonthly + (yearMonth ? `?year_month=${yearMonth}` : '')),

    list: (params: { limit?: number; briefing_type?: string } = {}): Promise<BriefingRead[]> =>
      get(AI_ENDPOINTS.briefer.list + buildQuery(params)),

    getById: (id: string): Promise<BriefingRead> =>
      get(AI_ENDPOINTS.briefer.getById(id)),
  },
};
