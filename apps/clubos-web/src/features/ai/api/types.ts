// TypeScript types matching ClubOS V2 Pydantic schemas.
// Field names are exact — do not rename without updating the backend schema.

// ── Shared ────────────────────────────────────────────────────────────────────

export type Confidence = 'high' | 'medium' | 'low';

export interface Citation {
  claim: string;
  source: string;
  section: string | null;
  quote: string | null;
}

// ── Scout ─────────────────────────────────────────────────────────────────────

export interface ScoutInput {
  question: string;
  user_id?: string | null;
  session_id?: string | null;
}

export interface ScoutAnswer {
  answer: string;
  citations: Citation[];
  confidence: Confidence;
  assumptions_made: string[];
  metrics_queried: string[];
  chunks_retrieved: number;
  retrieved_contexts: string[];
}

// ── Supervisor ────────────────────────────────────────────────────────────────

export type AgentType = 'scout' | 'investigator' | 'briefer' | 'unknown';

export type DispatchPath =
  | 'direct_scout'
  | 'direct_investigator'
  | 'direct_briefer'
  | 'langgraph_supervisor'
  | 'error';

export interface ClassificationResult {
  agent: AgentType;
  confidence: string;
  rule_matched: string | null;
  reasoning: string;
  extracted_params: Record<string, unknown>;
}

export interface SupervisorRequest {
  query: string;
  user_id?: string | null;
}

export interface SupervisorResponse {
  query: string;
  classification: ClassificationResult;
  dispatch_path: DispatchPath;
  result: Record<string, unknown>;
  latency_seconds: number;
  trace_url: string | null;
  error: string | null;
}

// ── Watchdog ──────────────────────────────────────────────────────────────────

export type AlertType =
  | 'new_in_top_n'
  | 'rank_jumped_into_top'
  | 'rank_dropped_significantly'
  | 'score_jump'
  | 'dropped_out_of_top_n'
  | 'persistent_top';

export type AlertSeverity = 'info' | 'warning' | 'critical';

export interface WatchdogAlertRead {
  alert_id: string;
  metric_name: string;
  alert_type: AlertType;
  severity: AlertSeverity;
  current_rank: number;
  previous_rank: number | null;
  rank_delta: number | null;
  score_current: number;
  score_previous: number | null;
  triggered_by_rule: string;
  context_snapshot: string;
  source: string;
  run_id: string;
  created_at: string;           // ISO datetime string
  acknowledged_at: string | null;
  acknowledged_by: string | null;
}

export interface WatchdogRunRequest {
  dedup_window_days?: number;
  top_n?: number;
  triggered_by?: string;
}

export interface WatchdogRunResponse {
  run_id: string;
  duration_seconds: number;
  metrics_evaluated: number;
  rules_fired: number;
  alerts_created: number;
  alerts_deduped: number;
  alert_ids: string[];
  errors: string[];
}

export interface AlertsListResponse {
  total: number;
  alerts: WatchdogAlertRead[];
  filters_applied: Record<string, unknown>;
}

export interface AcknowledgeResponse {
  alert_id: string;
  acknowledged_at: string | null;
  acknowledged_by: string | null;
}

// ── Investigator ──────────────────────────────────────────────────────────────

export type InvestigationStatus = 'running' | 'completed' | 'failed' | 'timeout';

export interface ReasoningStep {
  step_number: number;
  thought: string;
  action: string;
  action_input: Record<string, unknown>;
  observation: string;
}

export interface InvestigateRequest {
  triggered_by?: string;
  max_steps?: number;
}

export interface InvestigateResponse {
  investigation_id: string;
  alert_id: string;
  metric_name: string;
  status: string;
  finding: Record<string, unknown> | null;
  latency_seconds: number;
  trace_url: string | null;
  error: string | null;
}

export interface InvestigationRead {
  investigation_id: string;
  alert_id: string;
  metric_name: string;
  triggered_by: string;
  status: InvestigationStatus;
  cause_hypothesis: string | null;
  confidence: Confidence | null;
  evidence_summary: string | null;
  citations: Citation[];
  reasoning_trace: ReasoningStep[];
  tools_called: string[];
  total_steps: number | null;
  total_tokens: number | null;
  cost_usd: number | null;
  latency_seconds: number | null;
  trace_url: string | null;
  error_message: string | null;
  started_at: string;            // ISO datetime string
  completed_at: string | null;
}

export interface InvestigationListResponse {
  total: number;
  investigations: InvestigationRead[];
  filters_applied: Record<string, unknown>;
}

// ── Briefer ───────────────────────────────────────────────────────────────────

export type BriefingType =
  | 'monthly_scheduled'
  | 'ad_hoc_summary'
  | 'metric_focus'
  | 'incident_recap';

export type BriefingStatus = 'generating' | 'completed' | 'failed';

export interface BriefingContent {
  executive_summary: string;
  body_markdown: string;
  citations: Citation[];
  investigations_referenced: string[];
  alerts_referenced: string[];
  metrics_covered: string[];
}

export interface BriefingRunResult {
  briefing_id: string;
  briefing_type: BriefingType;
  scope_key: string;
  status: string;
  was_cached: boolean;
  content: BriefingContent | null;
  latency_seconds: number;
  total_tokens: number | null;
  cost_usd: number | null;
  trace_url: string | null;
  error: string | null;
}

export interface BriefingRead {
  briefing_id: string;
  briefing_type: BriefingType;
  scope_key: string;
  period_start: string;          // ISO datetime string
  period_end: string;
  triggered_by: string;
  status: BriefingStatus;
  executive_summary: string | null;
  body_markdown: string | null;
  citations: Citation[];
  investigations_referenced: string[];
  alerts_referenced: string[];
  metrics_covered: string[];
  total_tokens: number | null;
  cost_usd: number | null;
  latency_seconds: number | null;
  trace_url: string | null;
  freshness_days: number;
  error_message: string | null;
  started_at: string;
  completed_at: string | null;
}

// ── Narrowing helpers ─────────────────────────────────────────────────────────

export function isScoutResult(r: SupervisorResponse): r is SupervisorResponse & { result: ScoutAnswer } {
  return r.dispatch_path === 'direct_scout';
}

export function isBrieferResult(r: SupervisorResponse): r is SupervisorResponse & { result: BriefingRunResult } {
  return r.dispatch_path === 'direct_briefer';
}

export function isInvestigatorResult(r: SupervisorResponse): r is SupervisorResponse & { result: InvestigateResponse } {
  return r.dispatch_path === 'direct_investigator';
}

export function extractAnswerText(response: SupervisorResponse): string {
  const { dispatch_path, result } = response;
  if (dispatch_path === 'direct_scout') {
    return (result as unknown as ScoutAnswer).answer ?? JSON.stringify(result);
  }
  if (dispatch_path === 'direct_briefer') {
    const r = result as unknown as BriefingRunResult;
    return r.content?.executive_summary ?? r.content?.body_markdown ?? '(empty briefing)';
  }
  if (dispatch_path === 'direct_investigator') {
    const r = result as unknown as InvestigateResponse;
    const finding = r.finding as Record<string, unknown> | null;
    return (finding?.cause_hypothesis as string) ?? '(investigation running)';
  }
  if (dispatch_path === 'langgraph_supervisor') {
    return (result.final_synthesis as string) ?? JSON.stringify(result.step_results ?? result);
  }
  return response.error ?? '(no answer)';
}

export function extractCitations(response: SupervisorResponse): Citation[] {
  const { dispatch_path, result } = response;
  if (dispatch_path === 'direct_scout') {
    return (result as unknown as ScoutAnswer).citations ?? [];
  }
  if (dispatch_path === 'direct_briefer') {
    const r = result as unknown as BriefingRunResult;
    return r.content?.citations ?? [];
  }
  return [];
}
