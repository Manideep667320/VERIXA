export default function ConfidenceMeter({ confidence }: { confidence: number | null }) {
  const pct = confidence === null ? null : Math.round(Math.max(0, Math.min(1, confidence)) * 100)
  const descriptor =
    pct === null ? null : pct >= 80 ? 'High confidence' : pct >= 50 ? 'Moderate confidence' : 'Low confidence'

  return (
    <div className="rounded-lg border border-white/10 bg-white/[0.02] p-4">
      <div className="text-[10px] uppercase tracking-[0.14em] text-[var(--muted-text)] font-medium">
        Confidence
      </div>

      {pct === null ? (
        <p className="mt-3 text-[12px] leading-[1.6] text-[var(--muted-text)]">
          No confidence score yet.
        </p>
      ) : (
        <>
          <div className="mt-2 text-[26px] font-semibold text-white leading-none tabular-nums">
            {pct}%
          </div>
          <div className="mt-1 text-[12px] text-[var(--muted-text)]">{descriptor}</div>
          <div className="mt-2.5 h-1 w-full rounded-full bg-white/10 overflow-hidden">
            <div
              className="h-full rounded-full bg-white"
              style={{ width: `${pct}%` }}
            />
          </div>
        </>
      )}
    </div>
  )
}
