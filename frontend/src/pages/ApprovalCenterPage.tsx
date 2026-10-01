import { useEffect, useState } from 'react'
import AppShell from '@/components/shell/AppShell'
import StatusBadge from '@/components/StatusBadge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  approvalApi,
  policyApi,
  type PolicyVersionsResponse,
  type ApprovalRoute,
  type PendingApproval,
} from '@/services/api'

export default function ApprovalCenterPage() {
  const [policy, setPolicy] = useState<PolicyVersionsResponse | null>(null)

  const [approvalId, setApprovalId] = useState('')
  const [route, setRoute] = useState<ApprovalRoute | null>(null)
  const [lookupError, setLookupError] = useState<string | null>(null)
  const [busyAction, setBusyAction] = useState<string | null>(null)

  const [escalated, setEscalated] = useState<ApprovalRoute[] | null>(null)
  const [escalateError, setEscalateError] = useState<string | null>(null)
  const [isEscalating, setIsEscalating] = useState(false)
  const [pending, setPending] = useState<PendingApproval[]>([])
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  useEffect(() => {
    policyApi.versions().then(setPolicy).catch(() => setPolicy(null))
    approvalApi.pending().then((data) => {
      setPending(data)
      if (data.length > 0 && !approvalId) {
        selectApproval(data[0])
      }
    }).catch(() => setPending([]))
  }, [])

  const active = policy?.versions.find((v) => v.active)

  const selectApproval = async (item: PendingApproval) => {
    setApprovalId(item.approval_id)
    setLookupError(null)
    setSuccessMessage(null)
    if (item.current_role && item.roles) {
      setRoute({
        approval_id: item.approval_id,
        current_role: item.current_role,
        roles: item.roles,
        role_index: 0,
        human_queue: item.human_queue || 'human_queue',
        timeout_seconds: item.timeout_seconds || 900,
        expires_at: item.expires_at || null,
        status: item.route_status || 'PENDING',
        decided_by: null,
      })
    } else {
      setRoute(null)
    }
    try {
      const latest = await approvalApi.routing(item.approval_id)
      setRoute(latest)
    } catch {
      try {
        const routed = await approvalApi.route(item.approval_id)
        setRoute(routed)
      } catch {
        // keep existing route
      }
    }
  }

  const withBusy = async (label: string, fn: () => Promise<ApprovalRoute | unknown>) => {
    if (!approvalId.trim()) return
    setBusyAction(label)
    setLookupError(null)
    setSuccessMessage(null)
    try {
      const result = await fn()
      if (result && typeof result === 'object' && 'roles' in result) {
        setRoute(result as ApprovalRoute)
      }
      if (label === 'approve') {
        setSuccessMessage(`✓ Approval ${approvalId.trim()} successfully approved and executed! State verified.`)
        setPending((current) => current.filter((item) => item.approval_id !== approvalId.trim()))
        setRoute(null)
        setApprovalId('')
      } else if (label === 'reject') {
        setSuccessMessage(`✓ Approval ${approvalId.trim()} has been rejected.`)
        setPending((current) => current.filter((item) => item.approval_id !== approvalId.trim()))
        setRoute(null)
        setApprovalId('')
      }
    } catch (err) {
      setLookupError(err instanceof Error ? err.message : `${label} failed.`)
    } finally {
      setBusyAction(null)
    }
  }

  const getRiskBadge = (risk: string) => {
    const normalized = (risk || 'UNKNOWN').toUpperCase()
    if (normalized === 'HIGH') {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold border border-rose-500/40 bg-rose-500/15 text-rose-300">
          HIGH RISK
        </span>
      )
    }
    if (normalized === 'MEDIUM') {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold border border-amber-500/40 bg-amber-500/15 text-amber-300">
          MEDIUM RISK
        </span>
      )
    }
    if (normalized === 'LOW') {
      return (
        <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold border border-emerald-500/40 bg-emerald-500/15 text-emerald-300">
          LOW RISK
        </span>
      )
    }
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-semibold border border-white/20 bg-white/5 text-[var(--muted-text)]">
        UNKNOWN RISK
      </span>
    )
  }

  const escalateDue = async () => {
    setIsEscalating(true)
    setEscalateError(null)
    try {
      const result = await approvalApi.escalateDue()
      setEscalated(result.escalated)
    } catch (err) {
      setEscalateError(err instanceof Error ? err.message : 'Escalation check failed.')
    } finally {
      setIsEscalating(false)
    }
  }

  return (
    <AppShell contextLabel="Approval / Action Center" title="Approval Center">
      <div className="p-6 max-w-[900px] flex flex-col gap-5">
        <p className="text-[13px] leading-[1.6] text-[var(--muted-text)] max-w-[600px]">
          When the agent proposes an action above policy thresholds, it stops
          before execution and routes to a human — by role, with automatic
          timeout escalation and Slack or email sign-off.
        </p>

        {/* Approval lookup / actions */}
        <div className="rounded-lg border border-white/10 bg-white/[0.02] p-5">
          <div className="text-[10px] uppercase tracking-[0.14em] text-[var(--muted-text)] font-medium mb-1">
            Approval Lookup
          </div>
          <p className="text-[12.5px] text-[var(--muted-text)] mb-3">
            Select a pending request below, or enter an approval ID directly.
          </p>
          {pending.length > 0 && (
            <div className="mb-3 space-y-2">
              {pending.map((item) => {
                const amountVal = item.arguments?.amount ?? item.arguments?.cost
                return (
                  <button
                    key={item.approval_id}
                    type="button"
                    onClick={() => selectApproval(item)}
                    className={`w-full rounded-md border p-3 text-left transition-colors ${
                      approvalId === item.approval_id
                        ? 'border-amber-300/50 bg-amber-300/10'
                        : 'border-white/10 bg-black/20 hover:border-white/25'
                    }`}
                  >
                    <div className="flex items-center justify-between gap-3">
                      <span className="font-mono text-[11px] text-amber-200">{item.approval_id}</span>
                      <div className="flex items-center gap-2">
                        {amountVal !== undefined && (
                          <span className="font-mono text-[11px] text-amber-300/90 font-medium">
                            Cost: {typeof amountVal === 'number' ? `$${amountVal.toLocaleString()}` : String(amountVal)}
                          </span>
                        )}
                        {item.current_role && (
                          <span className="text-[10.5px] text-[var(--muted-text)]">
                            Assigned: <span className="text-white font-medium">{item.current_role.replace('_', ' ')}</span>
                          </span>
                        )}
                        {getRiskBadge(item.risk_level)}
                      </div>
                    </div>
                    <div className="mt-1 text-[12.5px] text-white font-medium capitalize">
                      {item.action_type.replaceAll('_', ' ')}
                    </div>
                    <div className="mt-1 text-[11.5px] leading-[1.5] text-[var(--muted-text)]">
                      {item.request}
                    </div>
                  </button>
                )
              })}
            </div>
          )}
          <div className="flex gap-2">
            <Input
              value={approvalId}
              onChange={(e) => {
                setApprovalId(e.target.value)
                setSuccessMessage(null)
              }}
              placeholder="APR-1042"
              className="bg-black/40 font-mono"
            />
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={!approvalId.trim() || busyAction !== null}
              onClick={() => withBusy('routing', () => approvalApi.routing(approvalId))}
            >
              {busyAction === 'routing' ? 'Checking…' : 'Check Routing'}
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={!approvalId.trim() || busyAction !== null}
              onClick={() => withBusy('route', () => approvalApi.route(approvalId))}
            >
              {busyAction === 'route' ? 'Routing…' : 'Route'}
            </Button>
            <Button
              type="button"
              size="sm"
              disabled={!approvalId.trim() || busyAction !== null}
              onClick={() => withBusy('approve', () => approvalApi.approve(approvalId))}
            >
              {busyAction === 'approve' ? 'Approving…' : 'Approve & Execute'}
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={!approvalId.trim() || busyAction !== null}
              onClick={() => withBusy('reject', () => approvalApi.reject(approvalId))}
            >
              {busyAction === 'reject' ? 'Rejecting…' : 'Reject'}
            </Button>
          </div>

          {lookupError && <p className="mt-3 text-[12.5px] text-[#f2635a]">{lookupError}</p>}
          {successMessage && <p className="mt-3 text-[12.5px] text-emerald-400 font-medium">{successMessage}</p>}

          {route && (
            <div className="mt-4 pt-4 border-t border-white/5 flex flex-col gap-2">
              <div className="flex items-center justify-between gap-3">
                <span className="text-[13px] text-white">{route.current_role}</span>
                <StatusBadge label={route.status} tone="warning" />
              </div>
              <div className="text-[11.5px] text-[var(--muted-text)]">
                Queue: {route.human_queue} · Timeout: {route.timeout_seconds}s · Roles:{' '}
                {route.roles.join(' → ')}
              </div>
            </div>
          )}
        </div>

        {/* Escalate overdue */}
        <div className="rounded-lg border border-white/10 bg-white/[0.02] p-5">
          <div className="flex items-center justify-between gap-4">
            <div>
              <div className="text-[10px] uppercase tracking-[0.14em] text-[var(--muted-text)] font-medium mb-1">
                Timeout Escalation
              </div>
              <p className="text-[12.5px] text-[var(--muted-text)]">
                Advance every timed-out pending approval to the next role.
              </p>
            </div>
            <Button type="button" variant="outline" onClick={escalateDue} disabled={isEscalating}>
              {isEscalating ? 'Checking…' : 'Escalate Overdue'}
            </Button>
          </div>
          {escalateError && <p className="mt-3 text-[12.5px] text-[#f2635a]">{escalateError}</p>}
          {escalated && (
            <p className="mt-3 text-[12.5px] text-[#c4c2c3]">
              {escalated.length === 0
                ? 'Nothing was overdue.'
                : `${escalated.length} approval(s) escalated.`}
            </p>
          )}
        </div>

        {active && (
          <div className="rounded-lg border border-white/10 bg-white/[0.02] p-5">
            <div className="text-[10px] uppercase tracking-[0.14em] text-[var(--muted-text)] font-medium mb-3">
              Active Policy · v{policy?.active_version}
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-lg border border-white/10 bg-black/20 p-3.5">
                <div className="text-[10px] uppercase tracking-[0.1em] text-[var(--muted-text)] mb-1">
                  Approval Threshold
                </div>
                <div className="text-[18px] font-semibold text-white">
                  ${active.approval_amount_threshold.toLocaleString()}
                </div>
              </div>
              <div className="rounded-lg border border-white/10 bg-black/20 p-3.5">
                <div className="text-[10px] uppercase tracking-[0.1em] text-[var(--muted-text)] mb-1">
                  Confidence Threshold
                </div>
                <div className="text-[18px] font-semibold text-white">
                  {Math.round(active.confidence_threshold * 100)}%
                </div>
              </div>
            </div>
            <p className="mt-3 text-[12px] text-[var(--muted-text)]">
              Actions above the amount threshold, or below the confidence
              threshold, route to a human approver instead of executing
              automatically.
            </p>
          </div>
        )}

        <div className="rounded-lg border border-white/10 bg-white/[0.02] p-5">
          <div className="text-[10px] uppercase tracking-[0.14em] text-[var(--muted-text)] font-medium mb-3">
            Routing Tiers
          </div>
          <div className="flex flex-col gap-2">
            <div className="flex items-center justify-between gap-3 rounded-lg border border-white/10 bg-black/20 px-3.5 py-2.5">
              <span className="text-[13px] text-white">High Risk</span>
              <span className="text-[11.5px] text-[var(--muted-text)]">
                Risk Director → Executive Approver
              </span>
              <StatusBadge label="Any Amount" tone="danger" />
            </div>
            <div className="flex items-center justify-between gap-3 rounded-lg border border-white/10 bg-black/20 px-3.5 py-2.5">
              <span className="text-[13px] text-white">High Amount</span>
              <span className="text-[11.5px] text-[var(--muted-text)]">
                Finance Manager → Executive Approver
              </span>
              <StatusBadge label="≥ $5,000" tone="warning" />
            </div>
            <div className="flex items-center justify-between gap-3 rounded-lg border border-white/10 bg-black/20 px-3.5 py-2.5">
              <span className="text-[13px] text-white">Default</span>
              <span className="text-[11.5px] text-[var(--muted-text)]">
                Service Manager → Operations Director
              </span>
              <StatusBadge label="Fallback" tone="neutral" />
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  )
}
