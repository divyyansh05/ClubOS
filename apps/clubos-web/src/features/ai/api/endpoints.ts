const BASE = '/api/ai';

export const AI_ENDPOINTS = {
  supervisor: {
    query: `${BASE}/supervisor/query`,
  },
  watchdog: {
    run: `${BASE}/watchdog/run`,
    alerts: `${BASE}/watchdog/alerts`,
    acknowledge: (alertId: string) => `${BASE}/watchdog/alerts/${alertId}/acknowledge`,
  },
  investigator: {
    run: (alertId: string) => `${BASE}/investigator/run/${alertId}`,
    list: `${BASE}/investigator`,
    getById: (id: string) => `${BASE}/investigator/${id}`,
  },
  briefer: {
    runMonthly: `${BASE}/briefer/run_monthly`,
    run: `${BASE}/briefer/run`,
    list: `${BASE}/briefer`,
    getById: (id: string) => `${BASE}/briefer/${id}`,
  },
} as const;
