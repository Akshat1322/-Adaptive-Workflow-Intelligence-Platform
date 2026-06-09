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
  datasetIntelligence: Record<string, unknown> | null
  workflow: { steps: WorkflowStep[] } | null
  leaderboard: ExperimentResult[]
  agentMessages: AgentMessage[]
  chatMessages: ChatMessage[]
  knowledgeResults: KnowledgeCard[]
  reportMarkdown: string | null
  orchestrationMetrics: Record<string, unknown> | null
  isOrchestrating: boolean
  isUploading: boolean
  setDatasetIntelligence: (data: Record<string, unknown>) => void
  setWorkflow: (workflow: { steps: WorkflowStep[] } | null) => void
  setLeaderboard: (leaderboard: ExperimentResult[]) => void
  setAgentMessages: (messages: AgentMessage[]) => void
  appendAgentMessage: (message: AgentMessage) => void
  clearAgentMessages: () => void
  appendChatMessage: (message: ChatMessage) => void
  clearChatMessages: () => void
  setKnowledgeResults: (results: KnowledgeCard[]) => void
  setReportMarkdown: (markdown: string | null) => void
  setOrchestrationMetrics: (metrics: Record<string, unknown> | null) => void
  setIsOrchestrating: (isOrchestrating: boolean) => void
  setIsUploading: (isUploading: boolean) => void
  applyOrchestrationResult: (data: {
    workflow?: { steps: WorkflowStep[] } | null
    leaderboard?: ExperimentResult[]
    results?: Record<string, unknown>
    report?: string | null
    messages?: AgentMessage[]
  }) => void
}

export const useWorkspaceStore = create<WorkspaceState>((set) => ({
  datasetIntelligence: null,
  workflow: null,
  leaderboard: [],
  agentMessages: [],
  chatMessages: [],
  knowledgeResults: [],
  reportMarkdown: null,
  orchestrationMetrics: null,
  isOrchestrating: false,
  isUploading: false,
  setDatasetIntelligence: (data) => set({ datasetIntelligence: data }),
  setWorkflow: (workflow) => set({ workflow }),
  setLeaderboard: (leaderboard) => set({ leaderboard }),
  setAgentMessages: (messages) => set({ agentMessages: messages }),
  appendAgentMessage: (message) =>
    set((state) => ({ agentMessages: [...state.agentMessages, message] })),
  clearAgentMessages: () => set({ agentMessages: [] }),
  appendChatMessage: (message) =>
    set((state) => ({ chatMessages: [...state.chatMessages, message] })),
  clearChatMessages: () => set({ chatMessages: [] }),
  setKnowledgeResults: (results) => set({ knowledgeResults: results }),
  setReportMarkdown: (markdown) => set({ reportMarkdown: markdown }),
  setOrchestrationMetrics: (metrics) => set({ orchestrationMetrics: metrics }),
  setIsOrchestrating: (isOrchestrating) => set({ isOrchestrating }),
  setIsUploading: (isUploading) => set({ isUploading }),
  applyOrchestrationResult: (data) =>
    set({
      workflow: data.workflow ?? null,
      leaderboard: data.leaderboard ?? [],
      orchestrationMetrics: data.results ?? null,
      reportMarkdown: data.report ?? null,
      agentMessages: data.messages ?? [],
    }),
}))
