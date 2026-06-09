import { useToastStore } from '@/store/toastStore'
import type { AgentMessage } from '@/store/workspaceStore'

export function getApiBase(): string {
  // If an explicit API URL is provided via environment variables (for production deployments like Vercel)
  if (process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL
  }
  
  // In the browser, use same-origin paths — Next.js rewrites proxy to the backend locally.
  if (typeof window !== 'undefined') {
    return ''
  }
  return 'http://127.0.0.1:8000'
}
export const BACKEND_UNAVAILABLE = 'Backend unavailable — start the server with start.bat'

export function isNetworkError(err: unknown): boolean {
  return err instanceof TypeError || (err instanceof Error && err.message.includes('fetch'))
}

export function showError(message: string) {
  useToastStore.getState().addToast({ type: 'error', message })
}

export function showSuccess(message: string) {
  useToastStore.getState().addToast({ type: 'success', message })
}

export async function apiFetch(
  path: string,
  options?: RequestInit,
  opts?: { errorMessage?: string; silent?: boolean }
): Promise<Response> {
  const silent = opts?.silent ?? false
  const errorMessage = opts?.errorMessage

  try {
    const res = await fetch(`${getApiBase()}${path}`, options)
    if (!res.ok) {
      let detail = `Request failed (${res.status})`
      if (res.status >= 500) {
        detail = BACKEND_UNAVAILABLE
      } else {
        try {
          const body = await res.json()
          if (body.error) detail = body.error
        } catch {
          // ignore parse errors
        }
      }
      if (!silent) showError(errorMessage ?? detail)
      throw new Error(detail)
    }
    return res
  } catch (err) {
    if (!silent) {
      if (isNetworkError(err)) {
        showError(BACKEND_UNAVAILABLE)
      } else if (errorMessage) {
        showError(errorMessage)
      }
    }
    throw err
  }
}

export interface OrchestrationResult {
  status: string
  workflow?: { steps: unknown[] } | null
  leaderboard?: { name: string; score: number }[]
  results?: Record<string, unknown>
  report?: string | null
  messages?: AgentMessage[]
  error?: string
}

export function streamOrchestration(handlers: {
  targetCol?: string
  onStarted?: () => void
  onMessage: (msg: AgentMessage) => void
  onComplete: (data: OrchestrationResult) => void
  onError: (error: string) => void
}): () => void {
  const apiBase = getApiBase()
  let url = `${apiBase}/api/orchestrate/stream`
  if (handlers.targetCol) {
    url += `?target_col=${encodeURIComponent(handlers.targetCol)}`
  }
  const es = new EventSource(url)
  let finished = false

  const cleanup = () => {
    finished = true
    es.close()
  }

  es.addEventListener('started', () => {
    handlers.onStarted?.()
  })

  es.addEventListener('agent_message', (e) => {
    try {
      const msg = JSON.parse((e as MessageEvent).data) as AgentMessage
      handlers.onMessage(msg)
    } catch {
      // ignore malformed events
    }
  })

  es.addEventListener('complete', (e) => {
    try {
      const data = JSON.parse((e as MessageEvent).data) as OrchestrationResult
      handlers.onComplete(data)
    } catch {
      handlers.onError('Failed to parse orchestration result')
    }
    cleanup()
  })

  es.addEventListener('error', (e) => {
    if (finished || es.readyState === EventSource.CLOSED) return

    const data = (e as MessageEvent).data
    if (data) {
      try {
        const parsed = JSON.parse(data)
        handlers.onError(parsed.error ?? 'Orchestration failed')
      } catch {
        handlers.onError('Orchestration failed')
      }
      cleanup()
      return
    }

    // No data: only treat as unavailable if we never connected
    if (es.readyState === EventSource.CONNECTING) {
      handlers.onError(BACKEND_UNAVAILABLE)
      cleanup()
    }
  })

  return cleanup
}
