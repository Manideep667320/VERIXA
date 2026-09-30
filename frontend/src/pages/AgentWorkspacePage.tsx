import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import AppShell from '@/components/shell/AppShell'
import RequestLibrary from '@/components/agent/RequestLibrary'
import AgentTimeline, { type AgentStep, type StepStatus } from '@/components/agent/AgentTimeline'
import EvidencePanel from '@/components/agent/EvidencePanel'
import ConfidenceMeter from '@/components/agent/ConfidenceMeter'
import RiskCard from '@/components/agent/RiskCard'
import PolicyStatus from '@/components/agent/PolicyStatus'
import StatusBadge, { type StatusTone } from '@/components/StatusBadge'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { shadowApi, type AgentState } from '@/services/api'
import { saveLastRun } from '@/lib/lastRun'

const STEP_DEFS = [
  {
    stage: 'understanding_request',
    title: 'Understanding request',
    description: 'Extracting intent and entities from the request.',
  },
  {
    stage: 'retrieving_evidence',
    title: 'Retrieving evidence',
    description: 'Searching SOPs, manuals, policies, and incident history.',
  },
  {
    stage: 'reasoning',
    title: 'Reasoning over evidence',
    description: 'Assessing evidence strength, conflicts, and confidence.',
  },
  {
    stage: 'preparing_action_plan',
    title: 'Preparing action plan',
    description: 'Assembling a structured, schema-validated action.',
  },
  {
    stage: 'evaluating_policy',
    title: 'Evaluating policy',
    description: 'Checking risk, permissions, and policy compliance.',
  },
  {
    stage: 'executing_actions',
    title: 'Executing actions',
    description: 'Running the authorized action through enterprise tools.',
  },
  {
    stage: 'verifying_outcome',
    title: 'Verifying outcome',
    description: "Confirming the executed action reached its intended state.",
  },
]

const DECISION_COPY: Record<string, { label: string; tone: StatusTone }> = {
  EXECUTE: { label: 'Executed', tone: 'success' },
  APPROVAL_REQUIRED: { label: 'Approval Required', tone: 'warning' },
  ESCALATE: { label: 'Escalated', tone: 'danger' },
}

function initialSteps(): AgentStep[] {
  return STEP_DEFS.map(({ stage: _stage, ...step }) => ({ ...step, status: 'queued' as const }))
}

function finalSteps(state: AgentState): AgentStep[] {
  return STEP_DEFS.map(({ stage, ...step }) => {
    const actualStatus = state.stage_statuses?.[stage] ?? 'queued'
    const status: StepStatus = actualStatus === 'queued' ? 'skipped' : actualStatus
    return { ...step, status }
  })
}

function runningSteps(): AgentStep[] {
  return STEP_DEFS.map(({ stage: _stage, ...step }, index) => {
    const status: StepStatus = index === 0 ? 'in_progress' : 'queued'
    return { ...step, status }
  })
}

export default function AgentWorkspacePage() {
  const navigate = useNavigate()
  const [requestText, setRequestText] = useState(
    'Customer reported Product X overheating. The customer is under warranty. Handle it.'
  )
  const [steps, setSteps] = useState<AgentStep[]>(initialSteps())
  const [isRunning, setIsRunning] = useState(false)
  const [response, setResponse] = useState<AgentState | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)

  const runAgent = async () => {
    if (!requestText.trim() || isRunning) return
    setIsRunning(true)
    setErrorMessage(null)
    setResponse(null)
    setSteps(runningSteps())

    try {
      const result = await shadowApi.run({ request: requestText, mode: 'shadow' })
      setResponse(result)
      saveLastRun(result)
      setSteps(finalSteps(result))
    } catch (err) {
      setErrorMessage(
        err instanceof Error ? err.message : 'Could not reach the agent service.'
      )
      setSteps(initialSteps())
    } finally {
      setIsRunning(false)
    }
  }

  const decisionCopy = response ? DECISION_COPY[response.autonomy_decision] : null

  return (
    <AppShell contextLabel="Agent Workspace" title="Evidence-to-Action Agent">
      <div className="grid grid-cols-1 lg:grid-cols-[260px_1fr_300px] gap-5 p-6">
        <RequestLibrary onUseExample={setRequestText} />

        <div className="min-w-0 flex flex-col gap-5">
          <div>
            <h2 className="text-[22px] font-semibold tracking-[-0.02em] text-white">
              Evidence-to-Action Agent
            </h2>
            <p className="mt-1 text-[13px] text-[var(--muted-text)]">
              Turn enterprise knowledge into verified actions.
            </p>
          </div>

          <div className="rounded-lg border border-white/10 bg-white/[0.02] p-4">
            <div className="text-[10px] uppercase tracking-[0.14em] text-[var(--muted-text)] font-medium mb-1">
              Agent Request
            </div>
            <div className="text-[12px] text-[var(--muted-text)] mb-2.5">
              Natural language input
            </div>
            <Textarea
              value={requestText}
              onChange={(e) => setRequestText(e.target.value)}
              rows={4}
              placeholder="Describe the request..."
              className="bg-black/40 text-[13.5px]"
            />
            <div className="mt-3 flex items-center justify-between gap-3">
              {errorMessage && (
                <p className="text-[12px] text-[#f2635a]">{errorMessage}</p>
              )}
              <Button
                type="button"
                onClick={runAgent}
                disabled={isRunning || !requestText.trim()}
                className="ml-auto"
              >
                {isRunning ? 'Running…' : 'Run Agent'}
              </Button>
            </div>
          </div>

          <div className="rounded-lg border border-white/10 bg-white/[0.02] p-4">
            <div className="flex items-center justify-between mb-1">
              <div className="text-[10px] uppercase tracking-[0.14em] text-[var(--muted-text)] font-medium">
                Agent Activity
              </div>
              {decisionCopy && (
                <StatusBadge label={decisionCopy.label} tone={decisionCopy.tone} />
              )}
            </div>
            <AgentTimeline steps={steps} />

            {response?.error && (
              <div
                role="alert"
                className="mt-3 rounded-md border border-[#f2635a]/30 bg-[#f2635a]/10 p-3 text-[12px] leading-[1.6] text-[#ff938b]"
              >
                Run stopped during {response.failed_stage?.replaceAll('_', ' ') ?? 'agent processing'}: {response.error}
              </div>
            )}

            {response?.reasoning_summary && (
              <div className="mt-3 pt-3 border-t border-white/5">
                <div className="text-[10px] uppercase tracking-[0.1em] text-[var(--muted-text)] font-medium mb-1">
                  Reasoning
                </div>
                <p className="text-[12.5px] leading-[1.6] text-[#c4c2c3]">
                  {response.reasoning_summary}
                </p>
              </div>
            )}

            {response?.final_response && (
              <p className="mt-3 pt-3 border-t border-white/5 text-[12px] leading-[1.6] text-[#a8a8a8]">
                {response.final_response}
              </p>
            )}

            {response && (
              <div className="mt-3 pt-3 border-t border-white/5 flex items-center justify-between">
                <span className="text-[11px] font-mono text-[var(--muted-text)]">
                  {response.run_id}
                </span>
                <Button
                  type="button"
                  variant="outline"
                  size="xs"
                  onClick={() => navigate('/decisions')}
                >
                  Review Full Decision
                </Button>
              </div>
            )}
          </div>
        </div>

        <div className="flex flex-col gap-4">
          <EvidencePanel evidence={response?.evidence ?? []} />
          <ConfidenceMeter confidence={response?.reasoning_summary ? response.evidence_confidence : null} />
          <RiskCard risk={response?.risk_level ?? null} />
          <PolicyStatus policy={response?.policy_result ?? null} />
        </div>
      </div>
    </AppShell>
  )
}
