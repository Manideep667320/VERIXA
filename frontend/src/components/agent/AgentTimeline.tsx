import { CheckCircle2, Loader2, Circle, AlertTriangle, PauseCircle } from 'lucide-react'
import StatusBadge from '@/components/StatusBadge'

export type StepStatus = 'complete' | 'in_progress' | 'queued' | 'waiting' | 'escalated'

export interface AgentStep {
  title: string
  description: string
  status: StepStatus
}

const STATUS_LABEL: Record<StepStatus, string> = {
  complete: 'Complete',
  in_progress: 'In Progress',
  queued: 'Queued',
  waiting: 'Awaiting Approval',
  escalated: 'Escalated',
}

function StepIcon({ status }: { status: StepStatus }) {
  if (status === 'complete') {
    return <CheckCircle2 size={16} strokeWidth={1.75} className="text-[#3ecf8e]" />
  }
  if (status === 'in_progress') {
    return <Loader2 size={16} strokeWidth={1.75} className="text-white animate-spin" />
  }
  if (status === 'waiting') {
    return <PauseCircle size={16} strokeWidth={1.75} className="text-[#f2b84b]" />
  }
  if (status === 'escalated') {
    return <AlertTriangle size={16} strokeWidth={1.75} className="text-[#f2635a]" />
  }
  return <Circle size={16} strokeWidth={1.75} className="text-[var(--muted-text)]" />
}

export default function AgentTimeline({ steps }: { steps: AgentStep[] }) {
  return (
    <div className="flex flex-col">
      {steps.map((step, i) => (
        <div
          key={step.title}
          className={`flex items-start gap-3 py-3 ${
            i < steps.length - 1 ? 'border-b border-white/5' : ''
          }`}
        >
          <div className="mt-0.5 shrink-0">
            <StepIcon status={step.status} />
          </div>
          <div className="min-w-0 flex-1">
            <div className="text-[13px] font-medium text-white">{step.title}</div>
            <div className="text-[12px] text-[var(--muted-text)] mt-0.5">
              {step.description}
            </div>
          </div>
          <StatusBadge
            label={STATUS_LABEL[step.status]}
            tone={
              step.status === 'complete'
                ? 'success'
                : step.status === 'in_progress'
                  ? 'info'
                  : step.status === 'waiting'
                    ? 'warning'
                    : step.status === 'escalated'
                      ? 'danger'
                      : 'neutral'
            }
            className="shrink-0 mt-0.5"
          />
        </div>
      ))}
    </div>
  )
}
