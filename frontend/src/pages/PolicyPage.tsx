import { useEffect, useState } from 'react'
import AppShell from '@/components/shell/AppShell'
import StatusBadge from '@/components/StatusBadge'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import {
  policyApi,
  type PolicyVersionsResponse,
  type PolicySimulationResult,
  type PolicyWriteResult,
} from '@/services/api'

const SAMPLE_CANDIDATE = `version: 2
confidence_threshold: 0.7
approval_amount_threshold: 10000
approval_risk_levels: [HIGH]
risk_levels:
  LOW: 0
  MEDIUM: 1
  HIGH: 2
  UNKNOWN: 3
actions:
  create_service_ticket: { allowed: true, risk_level: LOW, requires_approval: false }
  assign_technician: { allowed: true, risk_level: MEDIUM, requires_approval: false }
  replace_product: { allowed: true, risk_level: HIGH, requires_approval: true }
  issue_refund: { allowed: true, risk_level: HIGH, requires_approval: false, requires_approval_above: 50000 }
  send_notification: { allowed: true, risk_level: MEDIUM, requires_approval: false }
  lookup_customer: { allowed: true, risk_level: LOW, requires_approval: false }
approval_routing:
  timeout_seconds: 900
  human_queue: human_queue
  default_roles: [service_manager, operations_director]
  routes:
    - name: high_risk
      min_amount: 0
      risk_levels: [HIGH, UNKNOWN]
      approver_roles: [risk_director, executive_approver]
      priority: 20
    - name: high_amount
      min_amount: 10000
      risk_levels: [LOW, MEDIUM]
      approver_roles: [finance_manager, executive_approver]
      priority: 10
`

export default function PolicyPage() {
  const [versions, setVersions] = useState<PolicyVersionsResponse | null>(null)
  const [versionsError, setVersionsError] = useState<string | null>(null)

  const [candidateRules, setCandidateRules] = useState(SAMPLE_CANDIDATE)
  const [lastN, setLastN] = useState(100)
  const [simResult, setSimResult] = useState<PolicySimulationResult | null>(null)
  const [simError, setSimError] = useState<string | null>(null)
  const [isSimulating, setIsSimulating] = useState(false)

  const [publishRules, setPublishRules] = useState(SAMPLE_CANDIDATE)
  const [publishResult, setPublishResult] = useState<PolicyWriteResult | null>(null)
  const [publishError, setPublishError] = useState<string | null>(null)
  const [isPublishing, setIsPublishing] = useState(false)

  const loadVersions = () => {
    policyApi
      .versions()
      .then((v) => {
        setVersions(v)
        setVersionsError(null)
      })
      .catch((err) => setVersionsError(err instanceof Error ? err.message : 'Failed to load'))
  }

  useEffect(() => {
    loadVersions()
  }, [])

  const runSimulation = async () => {
    setIsSimulating(true)
    setSimError(null)
    setSimResult(null)
    try {
      const result = await policyApi.simulate(candidateRules, lastN)
      setSimResult(result)
    } catch (err) {
      setSimError(err instanceof Error ? err.message : 'Simulation failed.')
    } finally {
      setIsSimulating(false)
    }
  }

  const publish = async () => {
    setIsPublishing(true)
    setPublishError(null)
    setPublishResult(null)
    try {
      const result = await policyApi.publish(publishRules)
      setPublishResult(result)
      loadVersions()
    } catch (err) {
      setPublishError(err instanceof Error ? err.message : 'Publish failed.')
    } finally {
      setIsPublishing(false)
    }
  }

  return (
    <AppShell contextLabel="Policy Engine" title="Policy Versions & Simulation">
      <div className="p-6 max-w-[900px] flex flex-col gap-6">
        {/* Versions */}
        <div>
          <div className="text-[10px] uppercase tracking-[0.14em] text-[var(--muted-text)] font-medium mb-3">
            Policy Versions
          </div>
          {versionsError && <p className="text-[12.5px] text-[#f2635a]">{versionsError}</p>}
          {versions && (
            <div className="rounded-lg border border-white/10 bg-white/[0.02] divide-y divide-white/5">
              {versions.versions.map((v) => (
                <div key={v.version} className="flex items-center justify-between gap-4 px-4 py-3">
                  <span className="font-mono text-[13px] text-white">v{v.version}</span>
                  <span className="text-[11.5px] text-[var(--muted-text)]">
                    Approval &gt; ${v.approval_amount_threshold.toLocaleString()} · Confidence &gt;{' '}
                    {Math.round(v.confidence_threshold * 100)}%
                  </span>
                  {v.active && <StatusBadge label="Active" tone="success" />}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Simulate */}
        <div className="rounded-lg border border-white/10 bg-white/[0.02] p-5">
          <div className="text-[10px] uppercase tracking-[0.14em] text-[var(--muted-text)] font-medium mb-1">
            Simulate Policy Change
          </div>
          <p className="text-[12.5px] text-[var(--muted-text)] mb-3">
            Replay recent runs through a candidate ruleset — read-only, no LLM
            calls, nothing is applied.
          </p>
          <Textarea
            value={candidateRules}
            onChange={(e) => setCandidateRules(e.target.value)}
            rows={8}
            className="bg-black/40 font-mono text-[12px]"
          />
          <div className="mt-3 flex items-center gap-3">
            <label className="flex items-center gap-2 text-[12px] text-[var(--muted-text)]">
              Last N runs
              <input
                type="number"
                min={1}
                max={1000}
                value={lastN}
                onChange={(e) => setLastN(Number(e.target.value) || 100)}
                className="w-20 rounded-md border border-white/10 bg-black/40 px-2 py-1 text-white outline-none"
              />
            </label>
            <Button type="button" onClick={runSimulation} disabled={isSimulating} className="ml-auto">
              {isSimulating ? 'Simulating…' : 'Run Simulation'}
            </Button>
          </div>

          {simError && <p className="mt-3 text-[12.5px] text-[#f2635a]">{simError}</p>}

          {simResult && (
            <div className="mt-4 pt-4 border-t border-white/5">
              <p className="text-[12.5px] text-[#c4c2c3] mb-2">
                Checked {simResult.checked_runs} runs against policy v
                {simResult.policy_version} — {simResult.changed_decisions.length} decision
                {simResult.changed_decisions.length === 1 ? '' : 's'} would change.
              </p>
              {simResult.changed_decisions.length > 0 && (
                <div className="flex flex-col gap-1.5">
                  {simResult.changed_decisions.map((d) => (
                    <div
                      key={d.run_id}
                      className="flex items-center justify-between gap-3 rounded-md border border-white/10 bg-black/20 px-3 py-2 text-[12px]"
                    >
                      <span className="font-mono text-[var(--muted-text)]">{d.run_id}</span>
                      <span className="text-white">
                        {d.old} → {d.new}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Publish */}
        <div className="rounded-lg border border-white/10 bg-white/[0.02] p-5">
          <div className="text-[10px] uppercase tracking-[0.14em] text-[var(--muted-text)] font-medium mb-1">
            Publish New Policy Version
          </div>
          <p className="text-[12.5px] text-[var(--muted-text)] mb-3">
            Writes an immutable new version file and makes it active. Versions
            are never overwritten.
          </p>
          <Textarea
            value={publishRules}
            onChange={(e) => setPublishRules(e.target.value)}
            rows={8}
            className="bg-black/40 font-mono text-[12px]"
          />
          <div className="mt-3 flex items-center justify-between gap-3">
            {publishError && <p className="text-[12.5px] text-[#f2635a]">{publishError}</p>}
            <Button
              type="button"
              variant="outline"
              onClick={publish}
              disabled={isPublishing}
              className="ml-auto"
            >
              {isPublishing ? 'Publishing…' : 'Publish Version'}
            </Button>
          </div>
          {publishResult && (
            <p className="mt-3 text-[12.5px] text-[#3ecf8e]">
              Published v{publishResult.version} — now active.
            </p>
          )}
        </div>
      </div>
    </AppShell>
  )
}
