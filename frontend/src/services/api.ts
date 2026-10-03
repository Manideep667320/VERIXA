/**
 * API service layer — centralized backend communication.
 */

const API_BASE = (import.meta.env.VITE_API_URL ? String(import.meta.env.VITE_API_URL).replace(/\/$/, '') : '') + '/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!response.ok) {
    throw new Error(`API error: ${response.status} ${response.statusText}`);
  }
  return response.json();
}

// ── Shared domain types ──────────────────────────────────────────────────

export interface EvidenceItem {
  id: string;
  source: string;
  section: string;
  text: string;
  relevance_score: number;
  document_type: string;
  metadata: Record<string, unknown>;
}

export interface ActionContract {
  id: string;
  action_type: string;
  arguments: Record<string, unknown>;
  reason: string;
  evidence_ids: string[];
  risk_level: string;
  requires_approval: boolean;
  status: string;
}

export interface ActionResult {
  success: boolean;
  action_id: string;
  data: Record<string, unknown>;
  error: string | null;
}

export interface PolicyResult {
  allowed: boolean;
  requires_approval: boolean;
  risk_level: string;
  reason: string;
  matched_policy: string;
}

export interface AuditEvent {
  id: string;
  run_id: string;
  event_type: string;
  data: Record<string, unknown>;
  timestamp: string;
}

/** Full agent state — the real shape returned by the live agent pipeline. */
export interface AgentState {
  run_id: string;
  request: string;
  intent: string;
  entities: Record<string, unknown>;
  evidence: EvidenceItem[];
  evidence_confidence: number;
  reasoning_summary: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  proposed_actions: ActionContract[];
  policy_result: PolicyResult | null;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'UNKNOWN';
  autonomy_decision: 'EXECUTE' | 'APPROVAL_REQUIRED' | 'ESCALATE';
  approval_required: boolean;
  approval_id: string | null;
  execution_results: ActionResult[];
  verification_results: Record<string, unknown>[];
  final_response: string;
  status: string;
  error: string | null;
  workflow_mode: 'shadow' | 'supervised' | 'autonomous';
  failed_stage: string | null;
  stage_statuses: Record<string, 'queued' | 'complete' | 'failed' | 'skipped'>;
}

export type ChatIntent = 'DATA' | 'CONCEPT' | 'MIXED' | 'ACTION' | 'OUT_OF_SCOPE'

export interface ChatResponse {
  turn_id: string;
  thread_id: string;
  tenant_id: string;
  intent: ChatIntent;
  answer: string;
  sources: {
    help_ids: string[];
    knowledge_ids: string[];
    run_ids: string[];
  };
}

// ── Agent (legacy stub route — kept for compatibility) ──────────────────

export interface AgentRunRequest {
  request: string;
  user_id?: string;
}

export interface AgentRunResponse {
  run_id: string;
  status: string;
  decision: Record<string, unknown>;
  evidence: EvidenceItem[];
  actions: ActionContract[];
  approval_id?: string;
  final_response: string;
  audit_events: AuditEvent[];
}

export const agentApi = {
  run: (body: AgentRunRequest) =>
    request<AgentRunResponse>('/agent/run', { method: 'POST', body: JSON.stringify(body) }),

  getRun: (runId: string) =>
    request<AgentRunResponse>(`/agent/${runId}`),
};

export const chatApi = {
  turn: (message: string, threadId?: string) =>
    request<ChatResponse>('/chat/turn', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Tenant-ID': 'tenant-a',
      },
      body: JSON.stringify({ message, thread_id: threadId }),
    }),
};

// ── Shadow — the real, LLM-backed agent pipeline ─────────────────────────

export type WorkflowMode = 'shadow' | 'supervised' | 'autonomous'

export interface ShadowRunRequest {
  request: string;
  mode?: WorkflowMode;
}

export interface ShadowMismatch {
  run_id: string;
  request: string;
  human_decision: string;
  recommended_decision: string;
  human_action: string | null;
  recommended_actions: Record<string, unknown>[];
}

export interface ShadowReport {
  total_cases: number;
  matched_cases: number;
  match_rate: number;
  mismatches: ShadowMismatch[];
  escalation_rate: number;
  estimated_hours_saved: number;
}

export const shadowApi = {
  run: (body: ShadowRunRequest) =>
    request<AgentState>('/shadow/run', { method: 'POST', body: JSON.stringify(body) }),

  report: (minutesPerCase?: number) =>
    request<ShadowReport>(
      `/shadow/report${minutesPerCase ? `?minutes_per_case=${minutesPerCase}` : ''}`
    ),
};

// ── Approvals ──────────────────────────────────────────────────────────

export interface ApprovalRoute {
  approval_id: string;
  roles: string[];
  role_index: number;
  current_role: string;
  human_queue: string;
  timeout_seconds: number;
  expires_at: string | null;
  status: string;
  decided_by: string | null;
}

export interface PendingApproval {
  approval_id: string;
  run_id: string;
  request: string;
  reason: string;
  action_type: string;
  arguments: Record<string, unknown>;
  risk_level: string;
  decision: string;
  current_role?: string;
  roles?: string[];
  human_queue?: string;
  route_status?: string;
  expires_at?: string | null;
  timeout_seconds?: number;
}

export const approvalApi = {
  pending: () => request<PendingApproval[]>('/approvals/pending'),
  approve: (approvalId: string) =>
    request(`/approvals/${approvalId}/approve`, { method: 'POST' }),

  reject: (approvalId: string) =>
    request(`/approvals/${approvalId}/reject`, { method: 'POST' }),

  route: (approvalId: string) =>
    request<ApprovalRoute>(`/approvals/${approvalId}/route`, { method: 'POST' }),

  routing: (approvalId: string) =>
    request<ApprovalRoute>(`/approvals/${approvalId}/routing`),

  escalateDue: () =>
    request<{ escalated: ApprovalRoute[] }>('/approvals/escalate-due', { method: 'POST' }),
};

// ── Audit — tamper-evident hash chain ────────────────────────────────────

export interface ChainVerification {
  valid: boolean;
  first_broken_row_id: string | null;
  checked_rows: number;
}

export const auditApi = {
  getTrail: (runId: string) => request<AuditEvent[]>(`/audit/${runId}`),

  verifyChain: () => request<ChainVerification>('/audit/verify'),

  exportUrl: (format: 'json' | 'csv' = 'json') => `${API_BASE}/audit/export?format=${format}`,
};

// ── Policy — versioned, YAML-driven engine ───────────────────────────────

export interface PolicyVersionInfo {
  version: number;
  active: boolean;
  confidence_threshold: number;
  approval_amount_threshold: number;
  path: string;
}

export interface PolicyVersionsResponse {
  active_version: number;
  versions: PolicyVersionInfo[];
}

export interface DecisionChange {
  run_id: string;
  old: string;
  new: string;
  policy_version: number;
}

export interface PolicySimulationResult {
  policy_version: number;
  checked_runs: number;
  changed_decisions: DecisionChange[];
}

export interface PolicyWriteResult {
  version: number;
  active: boolean;
  confidence_threshold: number;
  approval_amount_threshold: number;
}

export const policyApi = {
  versions: () => request<PolicyVersionsResponse>('/policy/versions'),

  simulate: (candidateRules: string | Record<string, unknown>, lastN = 100) =>
    request<PolicySimulationResult>('/policy/simulate', {
      method: 'POST',
      body: JSON.stringify({ candidate_rules: candidateRules, last_n: lastN }),
    }),

  publish: (rules: string | Record<string, unknown>) =>
    request<PolicyWriteResult>('/policy', {
      method: 'POST',
      body: JSON.stringify({ rules }),
    }),
};

// ── Analytics ─────────────────────────────────────────────────────────

export interface AnalyticsSummary {
  from_date: string | null;
  to_date: string | null;
  total_runs: number;
  automation_rate: number;
  approval_rate: number;
  escalation_rate: number;
  verification_failure_rate: number;
  rollback_count: number;
  avg_decision_latency_seconds: number;
  hours_saved: number;
  cost_saved: number;
  minutes_per_case: number;
  cost_per_hour: number;
}

export const analyticsApi = {
  summary: (fromDate?: string, toDate?: string) => {
    const params = new URLSearchParams();
    if (fromDate) params.set('from', fromDate);
    if (toDate) params.set('to', toDate);
    const qs = params.toString();
    return request<AnalyticsSummary>(`/analytics/summary${qs ? `?${qs}` : ''}`);
  },
};

// ── Insights — human feedback loop ───────────────────────────────────────

export interface SopOverrideRate {
  sop_id: string;
  decisions: number;
  overrides: number;
  override_rate: number;
}

export interface KnowledgeGap {
  id: string;
  run_id: string;
  query: string;
  confidence: number;
  evidence_ids: string[];
  reason: 'NO_EVIDENCE' | 'BELOW_CONFIDENCE_THRESHOLD';
  detected_at: string;
}

export interface PolicyChangeSuggestion {
  id: string;
  policy_version: number;
  policy_field: string;
  current_value: number;
  suggested_value: number;
  reason_code: string;
  sop_ids: string[];
  rationale: string;
  status: string;
}

export interface InsightsReport {
  policy_version: number;
  sop_override_rates: SopOverrideRate[];
  knowledge_gaps: KnowledgeGap[];
  suggested_policy_changes: PolicyChangeSuggestion[];
}

export interface OverrideSubmission {
  run_id: string;
  reason_code: string;
  prompt?: string;
  decision?: string;
  actor: string;
  evidence_ids?: string[];
  policy_version?: number;
}

export interface FeedbackRecord {
  run_id: string;
  event_type: 'approval' | 'rejection' | 'override';
  reason_code: string;
  prompt: string;
  decision: string;
  actor: string;
  evidence_ids: string[];
  policy_version: number | null;
  id: string;
  created_at: string;
}

export const insightsApi = {
  get: () => request<InsightsReport>('/insights'),

  submitOverride: (body: OverrideSubmission) =>
    request<FeedbackRecord>('/insights/feedback/override', {
      method: 'POST',
      body: JSON.stringify(body),
    }),
};

// ── Health ──────────────────────────────────────────────────────────────

export const healthApi = {
  check: () => request<{ status: string; version: string }>('/health'),
};
