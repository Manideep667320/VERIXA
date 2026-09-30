import { useEffect, useState } from 'react'
import AppShell from '@/components/shell/AppShell'
import StatusBadge from '@/components/StatusBadge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  analyticsApi,
  insightsApi,
  shadowApi,
  type AnalyticsSummary,
  type InsightsReport,
  type ShadowReport,
} from '@/services/api'

function pct(value: number): string {
  return `${Math.round(value * 100)}%`
}

function KpiTile({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="rounded-lg border border-white/10 bg-white/[0.02] p-4">
      <div className="text-[10px] uppercase tracking-[0.12em] text-[var(--muted-text)] font-medium mb-1.5">
        {label}
      </div>
      <div className="text-[22px] font-semibold text-white tabular-nums leading-none">
        {value}
      </div>
      {sub && <div className="text-[11.5px] text-[var(--muted-text)] mt-1">{sub}</div>}
    </div>
  )
}

export default function InsightsPage() {
  const [fromDate, setFromDate] = useState('')
  const [toDate, setToDate] = useState('')
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null)
  const [insights, setInsights] = useState<InsightsReport | null>(null)
  const [shadow, setShadow] = useState<ShadowReport | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const [overrideRunId, setOverrideRunId] = useState('')
  const [overrideReason, setOverrideReason] = useState('')
  const [overrideActor, setOverrideActor] = useState('operations-manager')
  const [overrideSubmitting, setOverrideSubmitting] = useState(false)
  const [overrideMessage, setOverrideMessage] = useState<string | null>(null)

  const loadAnalytics = (from?: string, to?: string) => {
    setLoading(true)
    Promise.all([analyticsApi.summary(from, to), insightsApi.get(), shadowApi.report()])
      .then(([s, i, sh]) => {
        setSummary(s)
        setInsights(i)
        setShadow(sh)
        setError(null)
      })
      .catch((err) => {
        setError(err instanceof Error ? err.message : 'Could not load insights.')
      })
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadAnalytics()
  }, [])

  const submitOverride = async () => {
    if (!overrideRunId.trim() || !overrideReason.trim() || !overrideActor.trim()) return
    setOverrideSubmitting(true)
    setOverrideMessage(null)
    try {
      await insightsApi.submitOverride({
        run_id: overrideRunId.trim(),
        reason_code: overrideReason.trim(),
        actor: overrideActor.trim(),
      })
      setOverrideMessage('Recorded — refreshing insights.')
      setOverrideRunId('')
      setOverrideReason('')
      insightsApi.get().then(setInsights)
    } catch (err) {
      setOverrideMessage(err instanceof Error ? err.message : 'Failed to record override.')
    } finally {
      setOverrideSubmitting(false)
    }
  }

  return (
    <AppShell contextLabel="Operations Insights" title="Analytics & Insights">
      <div className="p-6 max-w-[1100px] flex flex-col gap-6">
        <div className="flex items-end gap-2">
          <label className="flex flex-col gap-1 text-[11px] text-[var(--muted-text)]">
            From
            <Input
              type="date"
              value={fromDate}
              onChange={(e) => setFromDate(e.target.value)}
              className="bg-black/40 w-[150px]"
            />
          </label>
          <label className="flex flex-col gap-1 text-[11px] text-[var(--muted-text)]">
            To
            <Input
              type="date"
              value={toDate}
              onChange={(e) => setToDate(e.target.value)}
              className="bg-black/40 w-[150px]"
            />
          </label>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => loadAnalytics(fromDate || undefined, toDate || undefined)}
          >
            Apply Range
          </Button>
        </div>

        {loading && (
          <p className="text-[13px] text-[var(--muted-text)]">Loading operational metrics…</p>
        )}
        {error && <p className="text-[13px] text-[#f2635a]">{error}</p>}

        {summary && (
          <div>
            <div className="text-[10px] uppercase tracking-[0.14em] text-[var(--muted-text)] font-medium mb-3">
              Operational Summary · {summary.total_runs} runs
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <KpiTile label="Automation Rate" value={pct(summary.automation_rate)} />
              <KpiTile label="Approval Rate" value={pct(summary.approval_rate)} />
              <KpiTile label="Escalation Rate" value={pct(summary.escalation_rate)} />
              <KpiTile
                label="Verification Failures"
                value={pct(summary.verification_failure_rate)}
              />
              <KpiTile label="Hours Saved" value={summary.hours_saved.toFixed(1)} />
              <KpiTile
                label="Cost Saved"
                value={`$${summary.cost_saved.toLocaleString(undefined, { maximumFractionDigits: 0 })}`}
              />
              <KpiTile
                label="Avg Decision Latency"
                value={`${summary.avg_decision_latency_seconds.toFixed(1)}s`}
              />
              <KpiTile label="Rollbacks" value={String(summary.rollback_count)} />
            </div>
          </div>
        )}

        {shadow && (
          <div>
            <div className="text-[10px] uppercase tracking-[0.14em] text-[var(--muted-text)] font-medium mb-3">
              Shadow Mode · Agent vs. Human
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <KpiTile label="Cases Compared" value={String(shadow.total_cases)} />
              <KpiTile label="Match Rate" value={pct(shadow.match_rate)} />
              <KpiTile label="Escalation Rate" value={pct(shadow.escalation_rate)} />
              <KpiTile
                label="Est. Hours Saved"
                value={shadow.estimated_hours_saved.toFixed(1)}
              />
            </div>
            {shadow.mismatches.length > 0 && (
              <div className="mt-3 flex flex-col gap-1.5">
                {shadow.mismatches.map((m) => (
                  <div
                    key={m.run_id}
                    className="flex items-center justify-between gap-3 rounded-md border border-white/10 bg-white/[0.02] px-3 py-2 text-[12px]"
                  >
                    <span className="font-mono text-[var(--muted-text)]">{m.run_id}</span>
                    <span className="text-white">
                      human: {m.human_decision} · agent: {m.recommended_decision}
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {insights && (
          <>
            <div>
              <div className="text-[10px] uppercase tracking-[0.14em] text-[var(--muted-text)] font-medium mb-3">
                SOP Override Rates
              </div>
              {insights.sop_override_rates.length === 0 ? (
                <div className="rounded-lg border border-white/10 bg-white/[0.02] p-4 text-[13px] text-[var(--muted-text)]">
                  No feedback recorded against any SOP yet.
                </div>
              ) : (
                <div className="rounded-lg border border-white/10 bg-white/[0.02] divide-y divide-white/5">
                  {insights.sop_override_rates.map((row) => (
                    <div
                      key={row.sop_id}
                      className="flex items-center justify-between gap-3 px-4 py-2.5"
                    >
                      <span className="font-mono text-[12.5px] text-white">{row.sop_id}</span>
                      <span className="text-[11.5px] text-[var(--muted-text)]">
                        {row.overrides} / {row.decisions} decisions overridden
                      </span>
                      <StatusBadge
                        label={pct(row.override_rate)}
                        tone={row.override_rate > 0.3 ? 'warning' : 'neutral'}
                      />
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div>
              <div className="text-[10px] uppercase tracking-[0.14em] text-[var(--muted-text)] font-medium mb-3">
                Knowledge Gaps
              </div>
              {insights.knowledge_gaps.length === 0 ? (
                <div className="rounded-lg border border-white/10 bg-white/[0.02] p-4 text-[13px] text-[var(--muted-text)]">
                  No knowledge gaps detected — every request found sufficient evidence.
                </div>
              ) : (
                <div className="flex flex-col gap-2">
                  {insights.knowledge_gaps.map((gap) => (
                    <div
                      key={gap.id}
                      className="rounded-lg border border-white/10 bg-white/[0.02] p-3.5 flex items-start justify-between gap-4"
                    >
                      <div className="min-w-0">
                        <div className="text-[13px] text-white truncate">{gap.query}</div>
                        <div className="text-[11.5px] text-[var(--muted-text)] mt-0.5">
                          Run {gap.run_id} · confidence {pct(gap.confidence)}
                        </div>
                      </div>
                      <StatusBadge
                        label={gap.reason.replace(/_/g, ' ')}
                        tone="warning"
                        className="shrink-0"
                      />
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div>
              <div className="text-[10px] uppercase tracking-[0.14em] text-[var(--muted-text)] font-medium mb-3">
                Suggested Policy Changes
              </div>
              {insights.suggested_policy_changes.length === 0 ? (
                <div className="rounded-lg border border-white/10 bg-white/[0.02] p-4 text-[13px] text-[var(--muted-text)]">
                  No policy changes suggested from operational feedback yet.
                </div>
              ) : (
                <div className="flex flex-col gap-2">
                  {insights.suggested_policy_changes.map((s) => (
                    <div
                      key={s.id}
                      className="rounded-lg border border-white/10 bg-white/[0.02] p-4"
                    >
                      <div className="flex items-center justify-between gap-3">
                        <span className="text-[13px] font-medium text-white">
                          {s.policy_field}: {s.current_value} → {s.suggested_value}
                        </span>
                        <StatusBadge label={s.status.replace(/_/g, ' ')} tone="warning" />
                      </div>
                      <p className="text-[12px] text-[#a8a8a8] mt-1.5 leading-[1.5]">
                        {s.rationale}
                      </p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}

        <div className="rounded-lg border border-white/10 bg-white/[0.02] p-5">
          <div className="text-[10px] uppercase tracking-[0.14em] text-[var(--muted-text)] font-medium mb-1">
            Record Human Override
          </div>
          <p className="text-[12.5px] text-[var(--muted-text)] mb-3">
            Log a decision an operator overrode — feeds the SOP override rates
            above. Never changes policy directly.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
            <Input
              value={overrideRunId}
              onChange={(e) => setOverrideRunId(e.target.value)}
              placeholder="Run ID"
              className="bg-black/40 font-mono"
            />
            <Input
              value={overrideReason}
              onChange={(e) => setOverrideReason(e.target.value)}
              placeholder="Reason code (e.g. APPROVAL_THRESHOLD_TOO_HIGH)"
              className="bg-black/40"
            />
            <Input
              value={overrideActor}
              onChange={(e) => setOverrideActor(e.target.value)}
              placeholder="Actor"
              className="bg-black/40"
            />
          </div>
          <div className="mt-3 flex items-center justify-between gap-3">
            {overrideMessage && (
              <p className="text-[12.5px] text-[#c4c2c3]">{overrideMessage}</p>
            )}
            <Button
              type="button"
              variant="outline"
              className="ml-auto"
              onClick={submitOverride}
              disabled={overrideSubmitting}
            >
              {overrideSubmitting ? 'Submitting…' : 'Submit Override'}
            </Button>
          </div>
        </div>
      </div>
    </AppShell>
  )
}
