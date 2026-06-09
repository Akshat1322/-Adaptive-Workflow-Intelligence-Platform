"use client"

import { motion, AnimatePresence } from "framer-motion"
import { BrainCircuit, Database, Beaker, LineChart, MessageSquare, ShieldAlert, Cpu } from "lucide-react"
import { useWorkspaceStore } from "@/store/workspaceStore"

export function AgentCollaboration() {
  const messages = useWorkspaceStore((state) => state.agentMessages)

  const getIcon = (agent: string) => {
    if (agent.includes("Data")) return <Database />
    if (agent.includes("Feature")) return <Beaker />
    if (agent.includes("Eval") || agent.includes("Drift")) return <LineChart />
    if (agent.includes("Model")) return <Cpu />
    if (agent.includes("Orchestrator")) return <ShieldAlert />
    return <BrainCircuit />
  }
  return (
    <div className="flex flex-col h-full">
      <h2 className="text-2xl font-bold text-slate-100 mb-6 flex items-center gap-3">
        <MessageSquare className="text-violet-400 w-6 h-6" />
        Agent Collaboration
      </h2>

      <div className="flex-1 overflow-y-auto space-y-8 relative px-4">
        <div className="absolute left-8 top-0 bottom-0 w-px bg-gradient-to-b from-slate-800 via-cyan-900/50 to-transparent" />
        
        <AnimatePresence>
          {messages.length === 0 && (
            <div className="text-center text-slate-500 mt-10">Waiting for agent collaboration to begin...</div>
          )}
          {messages.map((m, i) => (
            <motion.div 
              key={i}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="relative flex items-start gap-6"
            >
              <div className="relative z-10 w-10 h-10 rounded-full bg-slate-900 border border-slate-700 flex items-center justify-center text-cyan-400 shrink-0 shadow-[0_0_15px_rgba(6,182,212,0.15)]">
                {getIcon(m.sender)}
              </div>
              
              <div className="flex-1 bg-[#0b1021]/80 backdrop-blur-sm border border-slate-800/80 rounded-2xl p-4 shadow-lg">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-bold text-slate-200 uppercase tracking-wider">{m.sender}</span>
                  <span className="text-[10px] uppercase tracking-widest text-slate-500 font-semibold bg-slate-900/50 px-2 py-0.5 rounded">To: {m.recipient || "All"}</span>
                </div>
                <p className="text-slate-400 text-sm">{m.content}</p>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
    </div>
  )
}
