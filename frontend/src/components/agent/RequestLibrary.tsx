import { Button } from '@/components/ui/button'

export interface RequestTemplate {
  number: string
  title: string
  meta: string
  request: string
  expectedDecision: 'EXECUTE' | 'APPROVAL_REQUIRED' | 'ESCALATE'
}

export const REQUEST_TEMPLATES: RequestTemplate[] = [
  {
    number: '01',
    title: 'Autonomous execution',
    meta: 'Low risk / diagnostic service ticket',
    request:
      'Customer CUST-001 reports that Product X (PX-100) is overheating. Create a high-priority diagnostic service ticket with the overheating details.',
    expectedDecision: 'EXECUTE',
  },
  {
    number: '02',
    title: 'Human approval required',
    meta: 'High risk / replacement request',
    request:
      "The customer's machine has a severe failure. Arrange a replacement unit costing $6,000.",
    expectedDecision: 'APPROVAL_REQUIRED',
  },
  {
    number: '03',
    title: 'Safety escalation',
    meta: 'Insufficient evidence / Product Y',
    request:
      'The customer wants us to immediately replace Product Y because it is overheating.',
    expectedDecision: 'ESCALATE',
  },
  {
    number: '04',
    title: 'Conflicting warranty terms',
    meta: 'SOP-042 vs POL-WTY-001',
    request:
      'Determine whether the PX-100 repair is covered before dispatching a technician. SOP-042 states the warranty is 18 months, while POL-WTY-001 states it is 24 months.',
    expectedDecision: 'ESCALATE',
  },
  {
    number: '05',
    title: 'Conflicting overheating evidence',
    meta: 'Product X / warranty conflict',
    request:
      'Product X is overheating and the customer asks for immediate service. The available overheating SOP and corporate warranty policy disagree about the PX-100 warranty term. Decide whether to create a ticket and assign a technician.',
    expectedDecision: 'ESCALATE',
  },
  {
    number: '06',
    title: 'Conflicting replacement eligibility',
    meta: 'Replacement / unresolved coverage',
    request:
      'The customer requests a $6,000 replacement for a failed PX-100. The replacement policy permits replacement after a severe failure, but the warranty sources conflict about whether this unit is covered. Determine the next step.',
    expectedDecision: 'ESCALATE',
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
          {REQUEST_TEMPLATES.map((t) => (
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
