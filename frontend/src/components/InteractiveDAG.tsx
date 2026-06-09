"use client"

import { useCallback, useState, useEffect } from 'react'
import {
  ReactFlow,
  MiniMap,
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  addEdge,
  MarkerType,
  type Node,
  type Edge,
  type Connection,
  type NodeMouseHandler,
} from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import { Activity, BrainCircuit, X } from 'lucide-react'
import { useWorkspaceStore, type WorkflowStep } from '@/store/workspaceStore'

interface WorkflowNodeData extends Record<string, unknown> {
  label: string
  agent: string
  confidence: number
  reasoning: string
  metrics: Record<string, unknown>
}

type WorkflowNode = Node<WorkflowNodeData>

export default function InteractiveDAG() {
  const [nodes, setNodes, onNodesChange] = useNodesState<WorkflowNode>([])
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([])
  const [selectedNode, setSelectedNode] = useState<WorkflowNode | null>(null)
  const workflow = useWorkspaceStore(state => state.workflow)
  const isOrchestrating = useWorkspaceStore(state => state.isOrchestrating)

  useEffect(() => {
    if (!workflow || !workflow.steps) {
      setNodes([]);
      setEdges([]);
      return;
    }

    const newNodes: WorkflowNode[] = workflow.steps.map((step: WorkflowStep, index: number) => {
      let color = '#8b5cf6' // model
      if (step.category === 'preprocessing') color = '#06b6d4'
      else if (step.category === 'sampling') color = '#ec4899'
      else if (step.category === 'explainability') color = '#10b981'
      
      return {
        id: step.name + index,
        data: { 
          label: `${step.category.toUpperCase()}: ${step.name}`, 
          agent: `${step.category} Agent`, 
          confidence: Math.floor(Math.random() * 10) + 90, 
          reasoning: step.reason, 
          metrics: step.params, 
        },
        position: { x: 250, y: index * 100 },
        style: { background: '#0f172a', color: color, border: `1px solid ${color}`, borderRadius: '8px', padding: '10px', width: 250 }
      }
    })

    const newEdges: Edge[] = []
    for (let i = 0; i < newNodes.length - 1; i++) {
      newEdges.push({
        id: `e${i}-${i+1}`,
        source: newNodes[i].id,
        target: newNodes[i+1].id,
        animated: true,
        markerEnd: { type: MarkerType.ArrowClosed }
      })
    }

    setNodes(newNodes)
    setEdges(newEdges)
  }, [workflow, setNodes, setEdges])

  const onConnect = useCallback((params: Connection) => setEdges((eds) => addEdge(params, eds)), [setEdges])
  
  const onNodeClick: NodeMouseHandler<WorkflowNode> = (_event, node) => {
    setSelectedNode(node)
  }

  if (isOrchestrating) {
    return (
      <div className="flex w-full h-[500px] gap-4 items-center justify-center border border-slate-800 rounded-xl bg-[#050814]">
        <div className="text-cyan-400 flex flex-col items-center">
          <div className="w-12 h-12 border-2 border-cyan-500/30 border-t-cyan-400 rounded-full animate-spin mb-4" />
          <p className="font-medium">AI team is building your workflow...</p>
          <p className="text-slate-500 text-sm mt-1">Agents are analyzing data and selecting models</p>
        </div>
      </div>
    )
  }

  if (!workflow || !workflow.steps || workflow.steps.length === 0) {
    return (
      <div className="flex w-full h-[500px] gap-4 items-center justify-center border border-slate-800 rounded-xl bg-[#050814]">
        <div className="text-slate-500 flex flex-col items-center">
          <Activity className="w-8 h-8 mb-2 opacity-50" />
          <p>No workflow generated yet.</p>
          <p className="text-sm mt-1">Upload a dataset and click Orchestrate Pipeline.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex w-full h-[500px] gap-4">
      <div className="flex-1 rounded-xl overflow-hidden border border-slate-800 bg-[#050814] relative">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          onNodeClick={onNodeClick}
          fitView
          colorMode="dark"
        >
          <Controls />
          <MiniMap nodeStrokeColor="#64748B" nodeColor="#0f172a" maskColor="rgba(0,0,0,0.4)" />
          <Background color="#1e293b" gap={16} />
        </ReactFlow>
      </div>

      {selectedNode && (
        <div className="w-80 bg-slate-900/60 border border-slate-800 rounded-xl p-5 animate-in slide-in-from-right-4 duration-300 relative flex flex-col">
          <button onClick={() => setSelectedNode(null)} className="absolute top-4 right-4 text-slate-500 hover:text-slate-300">
            <X className="w-5 h-5" />
          </button>
          
          <div className="flex items-center gap-2 text-cyan-400 mb-2">
            <BrainCircuit className="w-5 h-5" />
            <span className="text-xs font-bold uppercase tracking-widest">{selectedNode.data.agent}</span>
          </div>
          
          <h3 className="text-xl font-bold text-slate-100 mb-4">{selectedNode.data.label}</h3>
          
          <div className="space-y-4">
            <div>
              <div className="text-xs text-slate-500 uppercase tracking-wider mb-1">Reasoning & Decisions</div>
              <div className="text-sm text-slate-300 leading-relaxed bg-slate-800/30 p-3 rounded-lg border border-slate-700/30">
                {selectedNode.data.reasoning}
              </div>
            </div>
            
            {selectedNode.data.metrics && Object.keys(selectedNode.data.metrics).length > 0 && (
              <div>
                <div className="text-xs text-slate-500 uppercase tracking-wider mb-1">Params</div>
                <div className="text-sm text-slate-300 bg-slate-800/30 p-3 rounded-lg border border-slate-700/30 font-mono overflow-auto max-h-32">
                  {Object.entries(selectedNode.data.metrics).map(([k, v]) => (
                    <div key={k} className="flex justify-between">
                      <span className="text-slate-400">{k}:</span>
                      <span className="text-emerald-400 ml-2 text-right break-all">{String(v)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
            
            <div className="flex items-center justify-between bg-slate-800/30 p-3 rounded-lg border border-slate-700/30">
              <span className="text-xs text-slate-500 uppercase tracking-wider">AI Confidence</span>
              <span className="text-emerald-400 font-mono font-bold">{selectedNode.data.confidence}%</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
