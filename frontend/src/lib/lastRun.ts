import type { AgentState } from '@/services/api'

const KEY = 'e2a:last-run'

export function saveLastRun(state: AgentState): void {
  try {
    sessionStorage.setItem(KEY, JSON.stringify(state))
  } catch {
    // sessionStorage unavailable — non-fatal, just skip persistence
  }
}

export function getLastRun(): AgentState | null {
  try {
    const raw = sessionStorage.getItem(KEY)
    return raw ? (JSON.parse(raw) as AgentState) : null
  } catch {
    return null
  }
}
