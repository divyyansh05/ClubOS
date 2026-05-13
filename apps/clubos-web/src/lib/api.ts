import type {
  PriorityListResponse,
  PriorityDetail,
  HealthSummary,
  BenchmarkResponse,
  SignalResponse,
  BriefingResponse,
} from "../types/clubos";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);
  if (!response.ok) {
    throw new Error(`Request failed for ${path}`);
  }
  return response.json() as Promise<T>;
}

export async function getLatestPriorities(): Promise<PriorityListResponse> {
  return fetchJson<PriorityListResponse>("/priorities/latest");
}

export async function getPriorityDetail(priorityId: string): Promise<PriorityDetail> {
  return fetchJson<PriorityDetail>(`/priorities/${priorityId}`);
}

export async function getHealthSummary(): Promise<HealthSummary> {
  return fetchJson<HealthSummary>("/health/summary");
}

export async function getBenchmark(asset: string, metric: string): Promise<BenchmarkResponse> {
  return fetchJson<BenchmarkResponse>(`/benchmark/${asset}/${metric}`);
}

export async function getSignals(): Promise<SignalResponse> {
  return fetchJson<SignalResponse>("/signals");
}

export async function getLatestBriefing(): Promise<BriefingResponse> {
  return fetchJson<BriefingResponse>("/briefing/latest");
}
