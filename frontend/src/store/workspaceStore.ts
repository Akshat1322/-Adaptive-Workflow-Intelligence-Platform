import { create } from 'zustand'

export interface WorkflowStep {
  id: string
  name: string
  category: string
  params: Record<string, unknown>
  reason: string
}

export interface AgentMessage {
  sender: string
  recipient?: string
  content: string
  timestamp: string
  confidence: number
  metadata: Record<string, unknown>
}

export interface ExperimentResult {
  name: string
  score: number
  metrics?: Record<string, unknown>
}

export interface KnowledgeCard {
  id?: string
  queryMatch: string
  dataset: string
  domain: string
  workflow: string
  performance: string
  insight: string
}

export interface ChatMessage {
  role: 'user' | 'assistant'
  content: string
  timestamp: string
  intent?: string
}

export interface WorkspaceState {
  activeView: 'explore' | 'pipeline' | 'results' | 'reasoning' | 'overview'
  datasetIntelligence: Record<string, unknown> | null
  workflow: { steps: WorkflowStep[] } | null
  leaderboard: ExperimentResult[]
  agentMessages: AgentMessage[]
  orchestrationMetrics: Record<string, unknown> | null
  isOrchestrating: boolean
  isUploading: boolean
  setActiveView: (view: 'explore' | 'pipeline' | 'results' | 'reasoning' | 'overview') => void
  setDatasetIntelligence: (data: Record<string, unknown>) => void
  setWorkflow: (workflow: { steps: WorkflowStep[] } | null) => void
  setLeaderboard: (leaderboard: ExperimentResult[]) => void
  setAgentMessages: (messages: AgentMessage[]) => void
  appendAgentMessage: (message: AgentMessage) => void
  clearAgentMessages: () => void
  setOrchestrationMetrics: (metrics: Record<string, unknown> | null) => void
  setIsOrchestrating: (isOrchestrating: boolean) => void
  setIsUploading: (isUploading: boolean) => void
  applyOrchestrationResult: (data: {
    workflow?: { steps: WorkflowStep[] } | null
    leaderboard?: ExperimentResult[]
    results?: Record<string, unknown>
    messages?: AgentMessage[]
  }) => void
}

export const useWorkspaceStore = create<WorkspaceState>((set) => ({
  activeView: 'explore',
  datasetIntelligence: null,
  workflow: null,
  leaderboard: [],
  agentMessages: [],
  orchestrationMetrics: null,
  isOrchestrating: false,
  isUploading: false,
  setActiveView: (view) => set({ activeView: view }),
  setDatasetIntelligence: (data) => set({ datasetIntelligence: data }),
  setWorkflow: (workflow) => set({ workflow }),
  setLeaderboard: (leaderboard) => set({ leaderboard }),
  setAgentMessages: (messages) => set({ agentMessages: messages }),
  appendAgentMessage: (message) =>
    set((state) => ({ agentMessages: [...state.agentMessages, message] })),
  clearAgentMessages: () => set({ agentMessages: [] }),
  setOrchestrationMetrics: (metrics) => set({ orchestrationMetrics: metrics }),
  setIsOrchestrating: (isOrchestrating) => set({ isOrchestrating }),
  setIsUploading: (isUploading) => set({ isUploading }),
  applyOrchestrationResult: (data) =>
    set({
      workflow: data.workflow ?? null,
      leaderboard: data.leaderboard ?? [],
      orchestrationMetrics: data.results ?? null,
      agentMessages: data.messages ?? [],
    }),
}))
