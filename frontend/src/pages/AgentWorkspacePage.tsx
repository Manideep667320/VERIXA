import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import AppShell from '@/components/shell/AppShell'
import { REQUEST_TEMPLATES } from '@/components/agent/RequestLibrary'
import AgentTimeline, { type AgentStep, type StepStatus } from '@/components/agent/AgentTimeline'
import EvidencePanel from '@/components/agent/EvidencePanel'
import ConfidenceMeter from '@/components/agent/ConfidenceMeter'
import RiskCard from '@/components/agent/RiskCard'
import PolicyStatus from '@/components/agent/PolicyStatus'
import StatusBadge, { type StatusTone } from '@/components/StatusBadge'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import {
  chatApi,
  shadowApi,
  type AgentState,
  type ChatResponse,
} from '@/services/api'
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
  const [selectedExample, setSelectedExample] = useState(0)
  const [steps, setSteps] = useState<AgentStep[]>(initialSteps())
  const [isRunning, setIsRunning] = useState(false)
  const [response, setResponse] = useState<AgentState | null>(null)
  const [errorMessage, setErrorMessage] = useState<string | null>(null)
  const [chatMessage, setChatMessage] = useState(REQUEST_TEMPLATES[0].request)
  const [chatHistory, setChatHistory] = useState<Array<{ message: string; response: ChatResponse }>>([])
  const [isChatting, setIsChatting] = useState(false)
  const [threadId, setThreadId] = useState<string>()

  const runAgent = async () => {
    const request = chatMessage.trim()
    if (!request || isRunning) return
    setIsRunning(true)
    setErrorMessage(null)
    setResponse(null)
    setSteps(runningSteps())

    try {
      const result = await shadowApi.run({ request, mode: 'autonomous' })
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

  const sendChatMessage = async () => {
    const message = chatMessage.trim()
    if (!message || isChatting) return
    setIsChatting(true)
    setErrorMessage(null)
    try {
      const result = await chatApi.turn(message, threadId)
      setChatHistory((current) => [...current, { message, response: result }])
      setThreadId(result.thread_id)
      setChatMessage('')
    } catch (err) {
      setErrorMessage(err instanceof Error ? err.message : 'Could not reach the chat service.')
    } finally {
      setIsChatting(false)
    }

  }

  const chooseExample = (index: number) => {
    setSelectedExample(index)
    setChatMessage(REQUEST_TEMPLATES[index].request)
  }

  const decisionCopy = response ? DECISION_COPY[response.autonomy_decision] : null

  return (
    <AppShell contextLabel="Agent Workspace" title="Evidence-to-Action Agent">
      <div className="grid grid-cols-1 lg:grid-cols-[1fr_300px] gap-5 p-6">
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
            <div className="flex items-center justify-between gap-3">
              <div>
                <div className="text-[10px] uppercase tracking-[0.14em] text-[var(--muted-text)] font-medium mb-1">
                  Agent conversation
                </div>
                <div className="text-[12px] text-[var(--muted-text)]">
                  Ask about warranty, policies, evidence, or audit records.
                </div>
              </div>
              <span className="rounded-full border border-emerald-400/30 px-2 py-1 text-[10px] uppercase tracking-[0.08em] text-emerald-300">
                Knowledge chat
              </span>
            </div>
            <div className="mt-4 max-h-[420px] min-h-[180px] space-y-3 overflow-y-auto scrollbar-hidden rounded-md border border-white/5 bg-black/20 p-3">
              {chatHistory.length === 0 ? (
                <p className="text-[12px] leading-[1.6] text-[var(--muted-text)]">
                  Start with a question such as “What does the warranty policy say about replacement?”
                </p>
              ) : (
                chatHistory.map(({ message, response: item }) => (
                  <div key={item.turn_id} className="space-y-2">
                    <div className="ml-8 rounded-md bg-white/[0.06] p-2.5 text-[12.5px] leading-[1.6] text-white">
                      {message}
                    </div>
                    <div className="mr-8 rounded-md border border-white/10 bg-black/30 p-2.5 text-[12.5px] leading-[1.6] text-[#c4c2c3]">
                      <p>{item.answer}</p>
                      {(item.sources.help_ids.length > 0 || item.sources.knowledge_ids.length > 0 || item.sources.run_ids.length > 0) && (
                        <div className="mt-2 text-[10px] text-[var(--muted-text)]">
                          Sources: {[...item.sources.help_ids, ...item.sources.knowledge_ids, ...item.sources.run_ids].join(', ')}
                        </div>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
            <div className="mt-3 flex items-center gap-2 overflow-x-auto scrollbar-hidden border-b border-white/10 pb-2">
              {REQUEST_TEMPLATES.map((template, index) => (
                <button
                  key={template.number}
                  type="button"
                  onClick={() => chooseExample(index)}
                  className={`shrink-0 rounded-md px-2.5 py-1.5 text-[10px] font-semibold uppercase tracking-[0.06em] transition-colors ${
                    selectedExample === index
                      ? 'bg-white text-black'
                      : 'border border-white/10 text-[var(--muted-text)] hover:border-white/25 hover:text-white'
                  }`}
                  title={template.meta}
                >
                  {template.number} · {template.title}
                </button>
              ))}
            </div>
            <div className="mt-2 flex items-center gap-2 text-[10px] uppercase tracking-[0.08em] text-[var(--muted-text)]">
              <span>Expected safety outcome:</span>
              <span
                className={
                  REQUEST_TEMPLATES[selectedExample].expectedDecision === 'EXECUTE'
                    ? 'text-emerald-300'
                    : REQUEST_TEMPLATES[selectedExample].expectedDecision === 'APPROVAL_REQUIRED'
                      ? 'text-amber-300'
                      : 'text-red-300'
                }
              >
                {REQUEST_TEMPLATES[selectedExample].expectedDecision.replace('_', ' ')}
              </span>
            </div>
            <div className="mt-3">
              <Textarea
                value={chatMessage}
                onChange={(event) => setChatMessage(event.target.value)}
                onKeyDown={(event) => {
                  if (event.key === 'Enter' && !event.shiftKey) {
                    event.preventDefault()
                    void runAgent()
                  }
                }}
                rows={3}
                placeholder="Ask about warranty and policy, or describe an action for the agent..."
                className="bg-black/40 text-[13.5px]"
              />
              <div className="mt-2 flex flex-wrap justify-end gap-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => void sendChatMessage()}
                  disabled={isChatting || isRunning || !chatMessage.trim()}
                >
                  {isChatting ? 'Asking…' : 'Ask Documentation'}
                </Button>
                <Button
                  type="button"
                  onClick={() => void runAgent()}
                  disabled={isRunning || isChatting || !chatMessage.trim()}
                >
                  {isRunning ? 'Running…' : 'Submit to Agent'}
                </Button>
              </div>
            </div>
          </div>

          <div className="rounded-lg border border-white/10 bg-white/[0.02] p-4">
            <div className="mt-3 flex items-center justify-between gap-3">
              {errorMessage && (
                <p className="text-[12px] text-[#f2635a]">{errorMessage}</p>
              )}
              <Button
                type="button"
                onClick={runAgent}
                disabled={isRunning || isChatting || !chatMessage.trim()}
                className="ml-auto"
              >
                {isRunning ? 'Running…' : 'Run Again'}
              </Button>
            </div>
          </div>

        </div>

        <div className="flex flex-col gap-4">
          <EvidencePanel evidence={response?.evidence ?? []} />
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
              <div role="alert" className="mt-3 rounded-md border border-[#f2635a]/30 bg-[#f2635a]/10 p-3 text-[12px] leading-[1.6] text-[#ff938b]">
                Run stopped during {response.failed_stage?.replaceAll('_', ' ') ?? 'agent processing'}: {response.error}
              </div>
            )}
            {response?.approval_id && (
              <div className="mt-3 rounded-md border border-amber-400/30 bg-amber-400/10 p-3 text-[12px] leading-[1.6] text-amber-100">
                <div className="font-medium">Waiting for human approval</div>
                <div className="mt-1 text-amber-100/80">
                  Approval <span className="font-mono">{response.approval_id}</span> is queued before the action can execute.
                </div>
                <Button type="button" variant="outline" size="xs" className="mt-2" onClick={() => navigate('/approvals')}>
                  Open Approval Center
                </Button>
              </div>
            )}
            {response?.reasoning_summary && (
              <div className="mt-3 pt-3 border-t border-white/5">
                <div className="text-[10px] uppercase tracking-[0.1em] text-[var(--muted-text)] font-medium mb-1">Reasoning</div>
                <p className="text-[12.5px] leading-[1.6] text-[#c4c2c3]">{response.reasoning_summary}</p>
              </div>
            )}
            {response?.final_response && (
              <p className="mt-3 pt-3 border-t border-white/5 text-[12px] leading-[1.6] text-[#a8a8a8]">{response.final_response}</p>
            )}
            {response && (
              <div className="mt-3 pt-3 border-t border-white/5 flex items-center justify-between">
                <span className="text-[11px] font-mono text-[var(--muted-text)]">{response.run_id}</span>
                <Button type="button" variant="outline" size="xs" onClick={() => navigate('/decisions')}>
                  Review Full Decision
                </Button>
              </div>
            )}
          </div>
          <ConfidenceMeter confidence={response?.reasoning_summary ? response.evidence_confidence : null} />
          <RiskCard risk={response?.risk_level ?? null} />
          <PolicyStatus policy={response?.policy_result ?? null} />
        </div>
      </div>
    </AppShell>
  )
}
