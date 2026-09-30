import { useEffect, useState, type ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import AppShell from '@/components/shell/AppShell'
import StatusBadge, { type StatusTone } from '@/components/StatusBadge'
import { Button } from '@/components/ui/button'
import { getLastRun } from '@/lib/lastRun'
import type { AgentState } from '@/services/api'

const RISK_TONE: Record<string, StatusTone> = {
  LOW: 'success',
  MEDIUM: 'warning',
  HIGH: 'danger',
  UNKNOWN: 'neutral',
}

const SEVERITY_TONE: Record<string, StatusTone> = {
  LOW: 'success',
  MEDIUM: 'warning',
  HIGH: 'danger',
  CRITICAL: 'danger',
}

const DECISION_TONE: Record<string, StatusTone> = {
  EXECUTE: 'success',
  APPROVAL_REQUIRED: 'warning',
  ESCALATE: 'danger',
}

function MetricTile({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="rounded-lg border border-white/10 bg-white/[0.02] p-3.5">
      <div className="text-[10px] uppercase tracking-[0.12em] text-[var(--muted-text)] font-medium mb-1.5">
        {label}
      </div>
      {children}
    </div>
  )
}

export default function DecisionReviewPage() {
  const navigate = useNavigate()
  const [run, setRun] = useState<AgentState | null | undefined>(undefined)

  useEffect(() => {
    setRun(getLastRun())
  }, [])

  if (run === undefined) {
    return (
      <AppShell contextLabel="Evidence & Decision" title="Decision Review">
        <div className="p-6" />
      </AppShell>
    )
  }

  if (run === null) {
    return (
      <AppShell contextLabel="Evidence & Decision" title="Decision Review">
        <div className="p-6">
          <div className="rounded-lg border border-white/10 bg-white/[0.02] p-8 text-center">
            <p className="text-[13px] text-[var(--muted-text)] mb-3">
              No run to review yet. Run the agent from the Workspace first.
            </p>
            <Button variant="outline" size="sm" onClick={() => navigate('/agent')}>
              Go to Agent Workspace
            </Button>
          </div>
        </div>
      </AppShell>
    )
  }

  const entities = Object.entries(run.entities ?? {})

  return (
    <AppShell contextLabel="Evidence & Decision" title="Decision Review">
      <div className="p-6 max-w-[1100px] flex flex-col gap-5">
        {/* Request summary */}
        <div className="rounded-lg border border-white/10 bg-white/[0.02] p-5">
          <div className="flex items-start justify-between gap-6 flex-wrap">
            <div className="min-w-0 flex-1">
              <div className="text-[10px] uppercase tracking-[0.14em] text-[var(--muted-text)] font-medium mb-2">
                Employee Request
              </div>
              <p className="text-[14.5px] leading-[1.6] text-white italic">
                “{run.request}”
              </p>
            </div>
            <div className="flex flex-wrap gap-4 text-[12.5px]">
              <div>
                <div className="text-[10px] uppercase tracking-[0.1em] text-[var(--muted-text)]">
                  Intent
                </div>
                <div className="text-white mt-0.5">{run.intent || '—'}</div>
              </div>
              <div>
                <div className="text-[10px] uppercase tracking-[0.1em] text-[var(--muted-text)]">
                  Severity
                </div>
                <StatusBadge
                  label={run.severity}
                  tone={SEVERITY_TONE[run.severity] ?? 'neutral'}
                  className="mt-1"
                />
              </div>
              <div>
                <div className="text-[10px] uppercase tracking-[0.1em] text-[var(--muted-text)]">
                  Run ID
                </div>
                <div className="font-mono text-[var(--muted-text)] mt-0.5">{run.run_id}</div>
              </div>
            </div>
          </div>
          {entities.length > 0 && (
            <div className="mt-4 pt-4 border-t border-white/5 flex flex-wrap gap-2">
              {entities.map(([key, value]) => (
                <span
                  key={key}
                  className="inline-flex items-center gap-1.5 rounded-md border border-white/10 bg-white/[0.03] px-2 py-1 text-[11px] text-[#c4c2c3]"
                >
                  <span className="text-[var(--muted-text)]">{key}:</span>
                  {String(value)}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Retrieved evidence */}
        <div>
          <div className="flex items-center justify-between mb-3">
            <div className="text-[10px] uppercase tracking-[0.14em] text-[var(--muted-text)] font-medium">
              Retrieved Evidence
            </div>
            <div className="text-[11px] text-[var(--muted-text)]">
              Coverage {run.evidence.length} · Confidence{' '}
              {Math.round(run.evidence_confidence * 100)}%
            </div>
          </div>
          {run.evidence.length === 0 ? (
            <div className="rounded-lg border border-white/10 bg-white/[0.02] p-5 text-[13px] text-[var(--muted-text)]">
              No evidence was retrieved for this request.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {run.evidence.map((item) => (
                <div
                  key={item.id}
                  className="rounded-lg border border-white/10 bg-white/[0.02] p-4"
                >
                  <div className="flex items-center justify-between gap-2">
                    <div className="text-[13.5px] font-medium text-white truncate">
                      {item.source}
                    </div>
                    <div className="text-[11px] text-[var(--muted-text)] shrink-0">
                      {Math.round(item.relevance_score * 100)}%
                    </div>
                  </div>
                  <div className="text-[11px] text-[var(--muted-text)] mt-0.5">
                    {item.document_type}
                    {item.section ? ` / ${item.section}` : ''}
                  </div>
                  {item.text && (
                    <p className="text-[12px] text-[#a8a8a8] mt-1.5 leading-[1.5] line-clamp-3">
                      {item.text}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* AI Decision metrics */}
        <div>
          <div className="text-[10px] uppercase tracking-[0.14em] text-[var(--muted-text)] font-medium mb-3">
            AI Decision
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <MetricTile label="Severity">
              <StatusBadge label={run.severity} tone={SEVERITY_TONE[run.severity] ?? 'neutral'} />
            </MetricTile>
            <MetricTile label="Confidence">
              <div className="text-[20px] font-semibold text-white tabular-nums">
                {Math.round(run.evidence_confidence * 100)}%
              </div>
            </MetricTile>
            <MetricTile label="Risk">
              <StatusBadge
                label={run.risk_level}
                tone={RISK_TONE[run.risk_level] ?? 'neutral'}
              />
            </MetricTile>
            <MetricTile label="Policy">
              <StatusBadge
                label={run.policy_result?.allowed ? 'Compliant' : 'Denied'}
                tone={run.policy_result?.allowed ? 'success' : 'danger'}
              />
            </MetricTile>
          </div>
        </div>

        {/* Decision summary */}
        <div className="rounded-lg border border-white/10 bg-white/[0.02] p-5">
          <div className="flex items-center justify-between mb-2">
            <div className="text-[10px] uppercase tracking-[0.14em] text-[var(--muted-text)] font-medium">
              Decision Summary
            </div>
            <StatusBadge
              label={run.autonomy_decision.replace('_', ' ')}
              tone={DECISION_TONE[run.autonomy_decision] ?? 'neutral'}
            />
          </div>
          <p className="text-[13.5px] leading-[1.6] text-white">
            {run.final_response || '—'}
          </p>
        </div>

        {/* Why this decision */}
        {run.reasoning_summary && (
          <div className="rounded-lg border border-white/10 bg-white/[0.02] p-5">
            <div className="text-[10px] uppercase tracking-[0.14em] text-[var(--muted-text)] font-medium mb-2">
              Why This Decision?
            </div>
            <p className="text-[13px] leading-[1.7] text-[#c4c2c3]">
              {run.reasoning_summary}
            </p>
            {run.policy_result?.matched_policy && (
              <p className="mt-2 text-[12px] text-[var(--muted-text)]">
                Matched policy: {run.policy_result.matched_policy}
                {run.policy_result.reason ? ` — ${run.policy_result.reason}` : ''}
              </p>
            )}
          </div>
        )}

        {/* Proposed actions */}
        {run.proposed_actions.length > 0 && (
          <div>
            <div className="text-[10px] uppercase tracking-[0.14em] text-[var(--muted-text)] font-medium mb-3">
              Proposed Actions
            </div>
            <div className="flex flex-col gap-2">
              {run.proposed_actions.map((action) => (
                <div
                  key={action.id}
                  className="rounded-lg border border-white/10 bg-white/[0.02] p-4 flex items-start justify-between gap-4"
                >
                  <div className="min-w-0">
                    <div className="text-[13.5px] font-medium text-white">
                      {action.action_type.replace(/_/g, ' ')}
                    </div>
                    <div className="text-[12px] text-[#a8a8a8] mt-0.5">{action.reason}</div>
                  </div>
                  <div className="flex items-center gap-2 shrink-0">
                    <StatusBadge
                      label={action.risk_level}
                      tone={RISK_TONE[action.risk_level] ?? 'neutral'}
                    />
                    {action.requires_approval && (
                      <StatusBadge label="Needs Approval" tone="warning" />
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </AppShell>
  )
}
