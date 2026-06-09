"use client"

import { useEffect, useRef } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Radio } from "lucide-react"
import { useWorkspaceStore } from "@/store/workspaceStore"
import { apiFetch } from "@/lib/api"

export function AgentFeed() {
  const messages = useWorkspaceStore((state) => state.agentMessages)
  const isOrchestrating = useWorkspaceStore((state) => state.isOrchestrating)
  const setMessages = useWorkspaceStore((state) => state.setAgentMessages)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (isOrchestrating) return

    const fetchFeed = async () => {
      try {
        const res = await apiFetch("/api/feed", undefined, { silent: true })
        const data = await res.json()
        if (data.messages?.length) {
          setMessages(data.messages)
        }
      } catch {
        // toast handled by apiFetch; skip silent fail on initial load
      }
    }

    if (messages.length === 0) {
      fetchFeed()
    }
  }, [isOrchestrating, messages.length, setMessages])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages.length, isOrchestrating])

  const agentStatus: Record<string, string> = {
    "Data Agent": "Idle",
    "Feature Agent": "Idle",
    "Model Agent": "Idle",
    "Orchestrator": "Idle",
    "Evaluation Agent": "Idle",
    "Explainability Agent": "Idle",
    "Reporting Agent": "Idle",
  }

  if (isOrchestrating) {
    const activeSenders = new Set(messages.map((m) => m.sender))
    for (const agent of Object.keys(agentStatus)) {
      if (activeSenders.has(agent)) {
        const agentMsgs = messages.filter((m) => m.sender === agent)
        const latest = agentMsgs[agentMsgs.length - 1]
        if (latest?.content.toLowerCase().includes("complete") || latest?.content.toLowerCase().includes("success")) {
          agentStatus[agent] = "Completed"
        } else {
          agentStatus[agent] = "Running"
        }
      }
    }
    if (messages.length > 0) {
      const latestSender = messages[messages.length - 1].sender
      if (agentStatus[latestSender] === "Idle") {
        agentStatus[latestSender] = "Thinking"
      }
    }
  } else if (messages.length > 0) {
    const latest = messages[messages.length - 1]
    if (latest.content.includes("complete") || latest.content.includes("Success")) {
      agentStatus[latest.sender] = "Completed"
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case "Completed": return "bg-emerald-500"
      case "Running": return "bg-blue-500 animate-pulse"
      case "Thinking": return "bg-amber-500 animate-pulse"
      case "Failed": return "bg-red-500"
      default: return "bg-slate-700"
    }
  }

  const activeAgents = Object.entries(agentStatus).filter(([, s]) => s !== "Idle")

  return (
    <div className="flex flex-col h-full">
      {isOrchestrating && (
        <div className="flex items-center gap-2 mb-3 px-2 py-1.5 bg-cyan-500/10 border border-cyan-500/20 rounded-lg shrink-0">
          <Radio className="w-3 h-3 text-cyan-400 animate-pulse" />
          <span className="text-[10px] uppercase tracking-wider font-bold text-cyan-400">Live Stream</span>
        </div>
      )}

      <div className="flex gap-2 mb-4 overflow-x-auto pb-2 scrollbar-hide shrink-0">
        {(activeAgents.length > 0 ? activeAgents : Object.entries(agentStatus).slice(0, 4)).map(([agent, status]) => (
          <div key={agent} className="flex items-center gap-1.5 bg-slate-900/50 border border-slate-800 rounded-lg px-2 py-1 text-[10px] uppercase tracking-wider font-semibold text-slate-400 shrink-0">
            <div className={`w-2 h-2 rounded-full ${getStatusColor(status)}`} />
            {agent.split(" ")[0]}
          </div>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto pr-2 space-y-4 relative">
        {messages.length === 0 && !isOrchestrating && (
          <div className="text-center text-slate-600 text-sm mt-10">
            Agents are currently idle.<br />Upload a dataset to begin.
          </div>
        )}
        {messages.length === 0 && isOrchestrating && (
          <div className="text-center text-cyan-400/70 text-sm mt-10 animate-pulse">
            Waiting for first agent message...
          </div>
        )}
        <AnimatePresence>
          {messages.map((msg, i) => {
            const time = msg.timestamp.split("T")[1]?.substring(0, 5) || "00:00"
            const color = msg.sender === "Orchestrator" ? "text-cyan-400" : "text-violet-400"
            const borderColor = msg.sender === "Orchestrator" ? "bg-cyan-500" : "bg-violet-500"

            return (
              <motion.div
                key={`${msg.timestamp}-${i}`}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.25 }}
                className="flex gap-3 text-sm group"
              >
                <div className="w-10 shrink-0 text-slate-500 text-xs font-mono pt-1">{time}</div>
                <div className="flex-1 pb-4 border-l border-slate-800/60 pl-3 relative group-last:border-transparent">
                  <div className={`absolute -left-[5px] top-1.5 w-2 h-2 rounded-full ${borderColor} shadow-[0_0_10px_rgba(0,0,0,0.5)]`} />
                  <div className={`font-semibold text-xs uppercase tracking-wide mb-1 ${color} flex justify-between`}>
                    {msg.sender}
                    {msg.confidence != null && (
                      <span className="text-emerald-400/80 bg-emerald-500/10 px-1 rounded">
                        {msg.confidence <= 1 ? Math.round(msg.confidence * 100) : Math.round(msg.confidence)}%
                      </span>
                    )}
                  </div>
                  <div className="text-slate-300 leading-relaxed bg-slate-900/30 p-2 rounded-md border border-slate-800/40">
                    {msg.content}
                  </div>
                </div>
              </motion.div>
            )
          })}
        </AnimatePresence>
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
