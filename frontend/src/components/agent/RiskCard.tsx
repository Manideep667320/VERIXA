import StatusBadge, { type StatusTone } from '@/components/StatusBadge'

const RISK_TONE: Record<string, StatusTone> = {
  LOW: 'success',
  MEDIUM: 'warning',
  HIGH: 'danger',
  UNKNOWN: 'neutral',
}

const RISK_COPY: Record<string, string> = {
  LOW: 'Within normal authority — no escalation required.',
  MEDIUM: 'Proceeds only if policy explicitly permits it.',
  HIGH: 'Requires human approval before any action executes.',
  UNKNOWN: 'Risk could not be established — the agent will escalate.',
}

export default function RiskCard({ risk }: { risk: string | null }) {
  const level = risk?.toUpperCase() ?? null

  return (
    <div className="rounded-lg border border-white/10 bg-white/[0.02] p-4">
      <div className="text-[10px] uppercase tracking-[0.14em] text-[var(--muted-text)] font-medium">
        Risk
      </div>

      {level === null ? (
        <p className="mt-3 text-[12px] leading-[1.6] text-[var(--muted-text)]">
          No risk assessment yet.
        </p>
      ) : (
        <>
          <div className="mt-2">
            <StatusBadge label={level} tone={RISK_TONE[level] ?? 'neutral'} />
          </div>
          <p className="mt-2 text-[12px] leading-[1.6] text-[#a8a8a8]">
            {RISK_COPY[level] ?? ''}
          </p>
        </>
      )}
    </div>
  )
}
