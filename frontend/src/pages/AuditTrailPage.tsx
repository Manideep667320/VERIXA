import { useState } from 'react'
import { ShieldCheck, ShieldAlert, Download } from 'lucide-react'
import AppShell from '@/components/shell/AppShell'
import StatusBadge from '@/components/StatusBadge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
  auditApi,
  agentApi,
  type ChainVerification,
  type AuditEvent,
  type AgentRunResponse,
} from '@/services/api'

export default function AuditTrailPage() {
  const [verification, setVerification] = useState<ChainVerification | null>(null)
  const [isVerifying, setIsVerifying] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [lookupId, setLookupId] = useState('')
  const [events, setEvents] = useState<AuditEvent[] | null>(null)
  const [lookupError, setLookupError] = useState<string | null>(null)
  const [isLookingUp, setIsLookingUp] = useState(false)

  const [legacyResult, setLegacyResult] = useState<AgentRunResponse | null>(null)
  const [legacyError, setLegacyError] = useState<string | null>(null)
  const [legacyBusy, setLegacyBusy] = useState<string | null>(null)

  const verify = async () => {
    setIsVerifying(true)
    setError(null)
    try {
      const result = await auditApi.verifyChain()
      setVerification(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not verify the audit chain.')
    } finally {
      setIsVerifying(false)
    }
  }

  const lookupRun = async () => {
    if (!lookupId.trim()) return
    setIsLookingUp(true)
    setLookupError(null)
    setEvents(null)
    try {
      setEvents(await auditApi.getTrail(lookupId.trim()))
    } catch (err) {
      setLookupError(err instanceof Error ? err.message : 'Lookup failed.')
    } finally {
      setIsLookingUp(false)
    }
  }

  const pingLegacyGetRun = async () => {
    if (!lookupId.trim()) return
    setLegacyBusy('get')
    setLegacyError(null)
    try {
      setLegacyResult(await agentApi.getRun(lookupId.trim()))
    } catch (err) {
      setLegacyError(err instanceof Error ? err.message : 'Request failed.')
    } finally {
      setLegacyBusy(null)
    }
  }

  const pingLegacyRun = async () => {
    setLegacyBusy('run')
    setLegacyError(null)
    try {
      setLegacyResult(await agentApi.run({ request: 'diagnostic ping' }))
    } catch (err) {
      setLegacyError(err instanceof Error ? err.message : 'Request failed.')
    } finally {
      setLegacyBusy(null)
    }
  }

  return (
    <AppShell contextLabel="Audit Trail" title="AI Audit Trail">
      <div className="p-6 max-w-[900px] flex flex-col gap-5">
        <p className="text-[13px] leading-[1.6] text-[var(--muted-text)] max-w-[600px]">
          Every run is appended to a SHA-256 hash-linked audit log — each row
          embeds the previous row's hash, so any tampering breaks the chain
          and is immediately detectable.
        </p>

        <div className="rounded-lg border border-white/10 bg-white/[0.02] p-5">
          <div className="flex items-center justify-between gap-4 flex-wrap">
            <div>
              <div className="text-[10px] uppercase tracking-[0.14em] text-[var(--muted-text)] font-medium mb-1">
                Chain Integrity
              </div>
              <p className="text-[12.5px] text-[var(--muted-text)]">
                Recompute every row's hash and confirm the chain has not been
                altered.
              </p>
            </div>
            <Button type="button" onClick={verify} disabled={isVerifying}>
              {isVerifying ? 'Verifying…' : 'Verify Chain Integrity'}
            </Button>
          </div>

          {error && <p className="mt-4 text-[12.5px] text-[#f2635a]">{error}</p>}

          {verification && (
            <div className="mt-4 pt-4 border-t border-white/5 flex items-center gap-3">
              {verification.valid ? (
                <ShieldCheck size={18} strokeWidth={1.75} className="text-[#3ecf8e]" />
              ) : (
                <ShieldAlert size={18} strokeWidth={1.75} className="text-[#f2635a]" />
              )}
              <div className="flex-1 min-w-0">
                <div className="text-[13px] text-white">
                  {verification.valid
                    ? `Chain verified — ${verification.checked_rows} rows checked, no tampering detected.`
                    : `Chain broken at row ${verification.first_broken_row_id}.`}
                </div>
              </div>
              <StatusBadge
                label={verification.valid ? 'Valid' : 'Broken'}
                tone={verification.valid ? 'success' : 'danger'}
              />
            </div>
          )}
        </div>

        <div className="rounded-lg border border-white/10 bg-white/[0.02] p-5">
          <div className="text-[10px] uppercase tracking-[0.14em] text-[var(--muted-text)] font-medium mb-1">
            Export Audit Log
          </div>
          <p className="text-[12.5px] text-[var(--muted-text)] mb-3">
            Download the full append-only audit trail for offline review or
            compliance records.
          </p>
          <div className="flex gap-2">
            <a href={auditApi.exportUrl('json')} target="_blank" rel="noreferrer">
              <Button type="button" variant="outline" size="sm">
                <Download size={13} strokeWidth={1.75} />
                Export JSON
              </Button>
            </a>
            <a href={auditApi.exportUrl('csv')} target="_blank" rel="noreferrer">
              <Button type="button" variant="outline" size="sm">
                <Download size={13} strokeWidth={1.75} />
                Export CSV
              </Button>
            </a>
          </div>
        </div>

        <div className="rounded-lg border border-white/10 bg-white/[0.02] p-5">
          <div className="text-[10px] uppercase tracking-[0.14em] text-[var(--muted-text)] font-medium mb-1">
            Look Up Run
          </div>
          <p className="text-[12.5px] text-[var(--muted-text)] mb-3">
            Fetch the audit events recorded for a specific run ID.
          </p>
          <div className="flex gap-2">
            <Input
              value={lookupId}
              onChange={(e) => setLookupId(e.target.value)}
              placeholder="RUN-1042"
              className="bg-black/40 font-mono"
            />
            <Button type="button" variant="outline" onClick={lookupRun} disabled={isLookingUp}>
              {isLookingUp ? 'Looking up…' : 'Look Up'}
            </Button>
          </div>
          {lookupError && <p className="mt-3 text-[12.5px] text-[#f2635a]">{lookupError}</p>}
          {events && (
            <div className="mt-3 pt-3 border-t border-white/5">
              {events.length === 0 ? (
                <p className="text-[12.5px] text-[var(--muted-text)]">
                  No events found for this run.
                </p>
              ) : (
                <div className="flex flex-col gap-1.5">
                  {events.map((e) => (
                    <div key={e.id} className="text-[12px] text-[#c4c2c3] font-mono">
                      {e.timestamp} · {e.event_type}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        <div className="rounded-lg border border-white/10 bg-white/[0.02] p-5">
          <div className="text-[10px] uppercase tracking-[0.14em] text-[var(--muted-text)] font-medium mb-1">
            Legacy Endpoints
          </div>
          <p className="text-[12.5px] text-[var(--muted-text)] mb-3">
            <code className="font-mono">/api/agent/run</code> and{' '}
            <code className="font-mono">/api/agent/&#123;run_id&#125;</code> predate the real
            pipeline and remain stubs — kept reachable here for completeness,
            not for production use.
          </p>
          <div className="flex gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={pingLegacyGetRun}
              disabled={!lookupId.trim() || legacyBusy !== null}
            >
              {legacyBusy === 'get' ? 'Pinging…' : 'GET /agent/{id}'}
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={pingLegacyRun}
              disabled={legacyBusy !== null}
            >
              {legacyBusy === 'run' ? 'Pinging…' : 'POST /agent/run'}
            </Button>
          </div>
          {legacyError && <p className="mt-3 text-[12.5px] text-[#f2635a]">{legacyError}</p>}
          {legacyResult && (
            <div className="mt-3 pt-3 border-t border-white/5 text-[12px] font-mono text-[#c4c2c3]">
              status: {legacyResult.status} · {legacyResult.final_response}
            </div>
          )}
        </div>
      </div>
    </AppShell>
  )
}
