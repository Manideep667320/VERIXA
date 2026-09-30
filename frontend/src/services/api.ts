/**
 * API service layer — centralized backend communication.
 */

const API_BASE = '/api';

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

// ── Agent ──────────────────────────────────────────────────────────────

export interface AgentRunRequest {
  request: string;
  user_id?: string;
}

export interface AgentRunResponse {
  run_id: string;
  status: string;
  decision: Record<string, unknown>;
  evidence: unknown[];
  actions: unknown[];
  approval_id?: string;
  final_response: string;
  audit_events: unknown[];
}

export const agentApi = {
  run: (body: AgentRunRequest) =>
    request<AgentRunResponse>('/agent/run', { method: 'POST', body: JSON.stringify(body) }),

  getRun: (runId: string) =>
    request<AgentRunResponse>(`/agent/${runId}`),
};

// ── Approvals ──────────────────────────────────────────────────────────

export const approvalApi = {
  approve: (approvalId: string) =>
    request(`/approvals/${approvalId}/approve`, { method: 'POST' }),

  reject: (approvalId: string) =>
    request(`/approvals/${approvalId}/reject`, { method: 'POST' }),
};

// ── Audit ──────────────────────────────────────────────────────────────

export const auditApi = {
  getTrail: (runId: string) =>
    request<unknown[]>(`/audit/${runId}`),
};

// ── Health ──────────────────────────────────────────────────────────────

export const healthApi = {
  check: () => request<{ status: string; version: string }>('/health'),
};
