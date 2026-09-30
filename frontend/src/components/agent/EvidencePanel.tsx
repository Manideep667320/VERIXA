import type { EvidenceItem } from '@/services/api'

function excerpt(text: string, max = 90): string {
  if (text.length <= max) return text
  return `${text.slice(0, max).trimEnd()}…`
}

export default function EvidencePanel({ evidence }: { evidence: EvidenceItem[] }) {
  const visible = evidence.slice(0, 3)
  const remaining = evidence.length - visible.length

  return (
    <div className="rounded-lg border border-white/10 bg-white/[0.02] p-4">
      <div className="flex items-center justify-between">
        <div className="text-[10px] uppercase tracking-[0.14em] text-[var(--muted-text)] font-medium">
          Evidence
        </div>
        <div className="text-[11px] text-[var(--muted-text)]">
          {evidence.length} {evidence.length === 1 ? 'record' : 'records'}
        </div>
      </div>

      {evidence.length === 0 ? (
        <p className="mt-3 text-[12px] leading-[1.6] text-[var(--muted-text)]">
          Run the agent to see retrieved evidence.
        </p>
      ) : (
        <div className="mt-3 flex flex-col gap-3">
          {visible.map((item) => (
            <div key={item.id} className="border-b border-white/5 pb-3 last:border-0 last:pb-0">
              <div className="flex items-center justify-between gap-2">
                <div className="text-[13px] font-medium text-white truncate">
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
                <p className="text-[12px] text-[#a8a8a8] mt-1 leading-[1.5]">
                  {excerpt(item.text)}
                </p>
              )}
            </div>
          ))}
          {remaining > 0 && (
            <div className="text-[11px] font-semibold uppercase tracking-[0.04em] text-[var(--muted-text)]">
              + {remaining} more {remaining === 1 ? 'source' : 'sources'}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
