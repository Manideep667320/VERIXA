import StatusBadge from '@/components/StatusBadge'

interface PolicyResult {
  allowed: boolean
  matched_policy?: string
  reason?: string
}

export default function PolicyStatus({ policy }: { policy: PolicyResult | null }) {
  return (
    <div className="rounded-lg border border-white/10 bg-white/[0.02] p-4">
      <div className="text-[10px] uppercase tracking-[0.14em] text-[var(--muted-text)] font-medium">
        Policy Status
      </div>

      {policy === null ? (
        <p className="mt-3 text-[12px] leading-[1.6] text-[var(--muted-text)]">
          No policy checked yet.
        </p>
      ) : (
        <div className="mt-2.5 flex items-center justify-between gap-2">
          <span className="text-[12.5px] text-white truncate">
            {policy.matched_policy || 'No matching policy'}
          </span>
          <StatusBadge
            label={policy.allowed ? 'Matched' : 'Denied'}
            tone={policy.allowed ? 'success' : 'danger'}
          />
        </div>
      )}
    </div>
  )
}
