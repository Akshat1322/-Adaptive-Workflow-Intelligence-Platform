"use client"

import { Activity, Beaker, BrainCircuit, Database, Radio } from "lucide-react"
import { useWorkspaceStore } from '@/store/workspaceStore'

function agentIcon(sender: string) {
  if (sender.includes("Data")) return <Database />
  if (sender.includes("Feature")) return <Beaker />
  if (sender.includes("Model")) return <BrainCircuit />
  return <Activity />
}

export function ReasoningTimeline() {
  const messages = useWorkspaceStore(state => state.agentMessages)
  const isOrchestrating = useWorkspaceStore(state => state.isOrchestrating)

  const timeline = messages.length > 0 
    ? messages.map(m => ({
        agent: m.sender,
        icon: agentIcon(m.sender),
        msg: "Agent Activity",
        desc: m.content,
        conf: Math.floor((m.confidence <= 1 ? m.confidence : m.confidence / 100) * 100)
      }))
    : [
        { agent: "System", icon: <Activity />, msg: "Waiting for Orchestration", desc: "Upload a dataset and click Orchestrate Pipeline to see the agent reasoning timeline.", conf: 100 }
      ]

  return (
    <div className="w-full bg-[#0b1021]/80 backdrop-blur-xl border border-slate-800 rounded-xl p-6 mt-6">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-bold text-slate-100">Execution & Reasoning Timeline</h3>
        {isOrchestrating && (
          <div className="flex items-center gap-2 text-cyan-400 text-xs font-bold uppercase tracking-wider">
            <Radio className="w-3 h-3 animate-pulse" />
            Live
          </div>
        )}
      </div>

      {isOrchestrating && messages.length === 0 && (
        <div className="flex items-center gap-3 text-cyan-400 mb-4">
          <div className="w-5 h-5 border-2 border-cyan-500/30 border-t-cyan-400 rounded-full animate-spin" />
          <span className="text-sm">Waiting for first agent message...</span>
        </div>
      )}
      
      <div className="flex flex-col space-y-0 relative">
        <div className="absolute left-6 top-6 bottom-6 w-0.5 bg-slate-800" />
        
        {timeline.map((step, i) => (
          <div key={i} className="flex gap-4 relative">
            <div className="w-12 h-12 rounded-full bg-slate-900 border-2 border-slate-800 flex items-center justify-center text-violet-400 z-10 shrink-0 shadow-[0_0_15px_rgba(139,92,246,0.15)] my-2">
              {step.icon}
            </div>
            
            <div className="flex-1 pb-8">
              <div className="bg-slate-900/60 border border-slate-800/80 rounded-xl p-4 transition-all hover:border-violet-500/50">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-xs font-bold text-slate-400 uppercase tracking-widest">{step.agent}</span>
                  <span className="text-emerald-400 font-mono text-xs bg-emerald-500/10 px-2 py-0.5 rounded">{step.conf}% Confidence</span>
                </div>
                <h4 className="text-slate-200 font-semibold mb-1">{step.msg}</h4>
                <p className="text-slate-400 text-sm leading-relaxed">{step.desc}</p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
