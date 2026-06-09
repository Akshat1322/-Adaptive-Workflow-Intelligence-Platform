import { streamOrchestration, showError, showSuccess } from '@/lib/api'
import { useWorkspaceStore, type WorkflowStep } from '@/store/workspaceStore'

export function runWorkspaceOrchestration(options?: {
  targetCol?: string
  onComplete?: () => void
  onStarted?: () => void
  successMessage?: string
}): () => void {
  const {
    setIsOrchestrating,
    clearAgentMessages,
    appendAgentMessage,
    applyOrchestrationResult,
  } = useWorkspaceStore.getState()

  setIsOrchestrating(true)
  clearAgentMessages()
  options?.onStarted?.()

  return streamOrchestration({
    targetCol: options?.targetCol,
    onMessage: (msg) => appendAgentMessage(msg),
    onComplete: (data) => {
      if (data.error) {
        showError(data.error)
      } else {
        applyOrchestrationResult({
          workflow: data.workflow as { steps: WorkflowStep[] } | null,
          leaderboard: data.leaderboard,
          results: data.results,
          messages: data.messages,
        })
        showSuccess(options?.successMessage ?? 'Pipeline orchestration complete')
      }
      setIsOrchestrating(false)
      options?.onComplete?.()
    },
    onError: (error) => {
      showError(error)
      setIsOrchestrating(false)
      options?.onComplete?.()
    },
  })
}
