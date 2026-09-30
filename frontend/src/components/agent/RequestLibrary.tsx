import { Button } from '@/components/ui/button'

interface RequestTemplate {
  number: string
  title: string
  meta: string
  request: string
}

const TEMPLATES: RequestTemplate[] = [
  {
    number: '01',
    title: 'Customer reports overheating',
    meta: 'Product X / warranty intake',
    request:
      'Customer reported Product X overheating. The customer is under warranty. Handle it.',
  },
  {
    number: '02',
    title: 'Resolve overdue service request',
    meta: 'Service queue / 4 days overdue',
    request:
      'Resolve the overdue service request in the queue — it is now 4 days past due.',
  },
  {
    number: '03',
    title: 'Check replacement eligibility',
    meta: 'Customer account / policy lookup',
    request:
      'Check replacement eligibility for this customer account under the current warranty policy.',
  },
  {
    number: '04',
    title: 'Investigate recurring incident',
    meta: 'Incident history / Product X',
    request:
      'Investigate the recurring overheating incidents reported for Product X over the last quarter.',
  },
]

interface RequestLibraryProps {
  onUseExample: (request: string) => void
}

export default function RequestLibrary({ onUseExample }: RequestLibraryProps) {
  return (
    <div className="flex flex-col gap-5">
      <div>
        <div className="text-[10px] uppercase tracking-[0.14em] text-[var(--muted-text)] font-medium mb-2.5">
          Request Library
        </div>
        <div className="flex flex-col gap-2">
          {TEMPLATES.map((t) => (
            <div
              key={t.number}
              className="rounded-lg border border-white/10 bg-white/[0.02] p-3"
            >
              <div className="flex items-start gap-2.5">
                <span className="font-mono text-[11px] text-[var(--muted-text)] pt-0.5 shrink-0">
                  {t.number}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="text-[13px] font-medium text-white leading-snug">
                    {t.title}
                  </div>
                  <div className="text-[11.5px] text-[var(--muted-text)] mt-0.5">
                    {t.meta}
                  </div>
                </div>
              </div>
              <Button
                type="button"
                variant="outline"
                size="xs"
                onClick={() => onUseExample(t.request)}
                className="mt-2.5 w-full text-[11px] font-semibold uppercase tracking-[0.04em]"
              >
                Use Example
              </Button>
            </div>
          ))}
        </div>
      </div>

      <div className="border-t border-white/10 pt-4">
        <div className="text-[10px] uppercase tracking-[0.14em] text-[var(--muted-text)] font-medium mb-2">
          Workspace Notes
        </div>
        <p className="text-[12px] leading-[1.6] text-[#a8a8a8]">
          Requests are matched against current SOPs, manuals, incidents, and
          policy documents before any action is proposed. Nothing executes
          without passing policy and risk control.
        </p>
      </div>
    </div>
  )
}
