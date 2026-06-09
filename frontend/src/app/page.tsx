"use client"

import { useRef, useState } from "react"
import type React from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Database, Folder, Beaker, FileText, Settings, Activity, Brain, Command, Play, RotateCcw, GitCompareArrows } from "lucide-react"
import InteractiveDAG from "@/components/InteractiveDAG"
import ExperimentLab from "@/components/ExperimentLab"
import DatasetIntelligence from "@/components/DatasetIntelligence"
import { CommandPalette } from "@/components/CommandPalette"
import { AgentFeed } from "@/components/AgentFeed"
import { AgentCollaboration } from "@/components/AgentCollaboration"
import { ReasoningTimeline } from "@/components/ReasoningTimeline"
import { KnowledgeBaseView } from "@/components/KnowledgeBase"
import { ReportStudio } from "@/components/ReportStudio"
import { DriftMonitor } from "@/components/DriftMonitor"
import { ToastContainer } from "@/components/ToastContainer"
import { apiFetch } from "@/lib/api"
import { runWorkspaceOrchestration } from "@/lib/orchestration"
import { useWorkspaceStore } from "@/store/workspaceStore"

export default function WorkspacePage() {
  const [activeTab, setActiveTab] = useState("home")
  const [isCommandOpen, setCommandOpen] = useState(false)
  const [chatInput, setChatInput] = useState("")
  const [isChatting, setIsChatting] = useState(false)
  const [autonomyMode, setAutonomyMode] = useState(false)
  const streamCleanupRef = useRef<(() => void) | null>(null)
  const chatMessages = useWorkspaceStore((state) => state.chatMessages)
  const appendChatMessage = useWorkspaceStore((state) => state.appendChatMessage)
  const isOrchestrating = useWorkspaceStore((state) => state.isOrchestrating)
  const workflow = useWorkspaceStore((state) => state.workflow)

  const handleChatSubmit = async () => {
    if (!chatInput.trim() || isChatting) return;
    const command = chatInput.trim()
    setIsChatting(true);
    appendChatMessage({
      role: "user",
      content: command,
      timestamp: new Date().toISOString(),
    })
    try {
      const res = await apiFetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command }),
      });
      const data = await res.json();
      appendChatMessage({
        role: "assistant",
        content: data.response || "I processed that request.",
        timestamp: new Date().toISOString(),
        intent: data.intent,
      })
      
      // Basic client-side navigation based on intent or response
      if (data.intent === "NAVIGATE" || data.intent === "GENERATE_REPORT") {
        if (command.toLowerCase().includes("report")) setActiveTab("reports");
        else if (command.toLowerCase().includes("experiment")) setActiveTab("experiments");
        else if (command.toLowerCase().includes("knowledge")) setActiveTab("knowledge");
        else setActiveTab("home");
      } else if (data.intent === "EXECUTE") {
        handleImprove("Copilot triggered a fresh orchestration run")
      }
      
      setChatInput("");
    } catch {
      // toast shown by apiFetch
    } finally {
      setIsChatting(false);
    }
  }

  const handleImprove = (successMessage = "Pipeline rerun complete") => {
    if (isOrchestrating) return
    setActiveTab("workflow")
    streamCleanupRef.current?.()
    streamCleanupRef.current = runWorkspaceOrchestration({
      successMessage,
      onComplete: () => {
        streamCleanupRef.current = null
      },
    })
  }

  return (
    <div className="flex h-screen w-full bg-[#050814] text-slate-200 font-sans overflow-hidden">
      
      {/* ── LEFT PANEL: Navigation ── */}
      <aside className="w-64 flex flex-col bg-[#0b1021]/80 backdrop-blur-xl border-r border-slate-800/80 p-4 shrink-0">
        <div className="flex items-center gap-2 mb-8 px-2">
          <div className="bg-gradient-to-r from-cyan-500 to-violet-500 p-1.5 rounded-md">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-cyan-400 to-violet-400 bg-clip-text text-transparent">AWIP</span>
        </div>

        <nav className="flex-1 space-y-1">
          <NavItem icon={<Database />} label="Datasets" active={activeTab === "home"} onClick={() => setActiveTab("home")} />
          <NavItem icon={<Activity />} label="Workflow Canvas" active={activeTab === "workflow"} onClick={() => setActiveTab("workflow")} />
          <NavItem icon={<Brain />} label="Team Comms" active={activeTab === "comms"} onClick={() => setActiveTab("comms")} />
          <NavItem icon={<Beaker />} label="Experiment Lab" active={activeTab === "experiments"} onClick={() => setActiveTab("experiments")} />
          <NavItem icon={<Folder />} label="Knowledge Base" active={activeTab === "knowledge"} onClick={() => setActiveTab("knowledge")} />
          <NavItem icon={<GitCompareArrows />} label="Drift Monitor" active={activeTab === "drift"} onClick={() => setActiveTab("drift")} />
          <NavItem icon={<FileText />} label="Reports" active={activeTab === "reports"} onClick={() => setActiveTab("reports")} />
        </nav>

        <div className="mt-auto space-y-2">
          <div className="px-3 py-2 flex items-center justify-between bg-slate-900/50 rounded-lg border border-slate-800">
            <div className="flex flex-col">
              <span className="text-xs font-semibold text-slate-300">Autonomy Mode</span>
              <span className="text-[10px] text-slate-500">Auto-execute workflows</span>
            </div>
            <button 
              onClick={() => setAutonomyMode(!autonomyMode)}
              className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${autonomyMode ? 'bg-cyan-500' : 'bg-slate-700'}`}
            >
              <span className={`inline-block h-3 w-3 transform rounded-full bg-white transition-transform ${autonomyMode ? 'translate-x-5' : 'translate-x-1'}`} />
            </button>
          </div>
          <NavItem icon={<Settings />} label="Settings" active={activeTab === "settings"} onClick={() => setActiveTab("settings")} />
        </div>
      </aside>

      {/* ── CENTER PANEL: Workspace ── */}
      <main className="flex-1 flex flex-col relative overflow-hidden bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-slate-900/40 via-[#050814] to-[#050814]">
        
        {/* Top Command Bar Trigger */}
        <header className="h-16 flex items-center justify-center px-6 border-b border-slate-800/40 shrink-0">
          <button 
            onClick={() => setCommandOpen(true)}
            className="flex items-center gap-2 px-4 py-2 w-96 max-w-full bg-slate-900/50 hover:bg-slate-800/60 border border-slate-700/50 rounded-xl text-slate-400 text-sm transition-all focus:outline-none focus:ring-2 focus:ring-violet-500/50"
          >
            <Command className="w-4 h-4" />
            <span>Search or type a command...</span>
            <div className="ml-auto flex gap-1">
              <kbd className="px-1.5 py-0.5 bg-slate-800 rounded text-[10px] font-medium font-mono">Ctrl</kbd>
              <kbd className="px-1.5 py-0.5 bg-slate-800 rounded text-[10px] font-medium font-mono">K</kbd>
            </div>
          </button>
        </header>

        <CommandPalette open={isCommandOpen} setOpen={setCommandOpen} onNavigate={setActiveTab} />

        {/* Dynamic Canvas */}
        <div className="flex-1 overflow-y-auto p-6 relative">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
              className="h-full"
            >
              {activeTab === "home" && <DatasetIntelligenceView onOrchestrate={() => setActiveTab("workflow")} autonomyMode={autonomyMode} />}
              {activeTab === "workflow" && (
                <div className="h-full flex flex-col overflow-y-auto pr-2 pb-10">
                  <h1 className="text-2xl font-bold text-slate-100 mb-6 shrink-0">Interactive Workflow DAG</h1>
                  <InteractiveDAG />
                  <ReasoningTimeline />
                </div>
              )}
              {activeTab === "comms" && <AgentCollaboration />}
              {activeTab === "experiments" && <ExperimentLabView />}
              {activeTab === "knowledge" && <KnowledgeBaseView />}
              {activeTab === "drift" && <DriftMonitor />}
              {activeTab === "reports" && <ReportStudio />}
            </motion.div>
          </AnimatePresence>
        </div>
      </main>

      {/* ── RIGHT PANEL: AI Headquarters ── */}
      <aside className="w-80 flex flex-col bg-[#0b1021]/80 backdrop-blur-xl border-l border-slate-800/80 p-4 shrink-0">
        <div className="flex items-center gap-2 mb-6 px-2 text-cyan-400">
          <Activity className="w-5 h-5" />
          <span className="font-semibold text-sm uppercase tracking-wider">AI Copilot</span>
        </div>

        <div className="flex-1 overflow-y-auto rounded-lg bg-slate-900/40 border border-slate-800/60 p-3 space-y-4">
          {chatMessages.length > 0 && (
            <div className="space-y-2 border-b border-slate-800/70 pb-4">
              <div className="text-[10px] uppercase tracking-wider font-bold text-slate-500">Copilot Conversation</div>
              {chatMessages.slice(-4).map((msg, i) => (
                <div
                  key={`${msg.timestamp}-${i}`}
                  className={`rounded-lg border p-2 text-xs leading-relaxed ${
                    msg.role === "user"
                      ? "bg-cyan-500/10 border-cyan-500/20 text-cyan-100"
                      : "bg-violet-500/10 border-violet-500/20 text-slate-200"
                  }`}
                >
                  <div className="mb-1 font-bold uppercase tracking-wider text-[10px] opacity-70">
                    {msg.role === "user" ? "You" : `Copilot${msg.intent ? ` · ${msg.intent}` : ""}`}
                  </div>
                  {msg.content}
                </div>
              ))}
            </div>
          )}
          <AgentFeed />
        </div>

        <div className="mt-4 shrink-0">
          {workflow?.steps?.length ? (
            <button
              onClick={() => handleImprove("Pipeline improvement run complete")}
              disabled={isOrchestrating}
              className="mb-3 w-full flex items-center justify-center gap-2 bg-slate-900/80 hover:bg-slate-800 disabled:opacity-50 border border-slate-700/60 text-slate-300 px-3 py-2 rounded-xl text-sm transition-colors"
            >
              <RotateCcw className="w-4 h-4" />
              {isOrchestrating ? "Improving..." : "Run Again / Improve"}
            </button>
          ) : null}
          <div className="relative">
            <input 
              type="text" 
              placeholder="Ask the AI team..." 
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyDown={(e) => { if (e.key === 'Enter') handleChatSubmit(); }}
              disabled={isChatting}
              className="w-full bg-slate-900/80 border border-slate-700/60 rounded-xl pl-4 pr-10 py-3 text-sm text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50"
            />
            <button 
              onClick={handleChatSubmit}
              disabled={isChatting}
              className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 text-slate-400 hover:text-cyan-400 transition-colors disabled:opacity-50">
              <Play className="w-4 h-4" />
            </button>
          </div>
        </div>
      </aside>

      <ToastContainer />
    </div>
  )
}

function NavItem({
  icon,
  label,
  active,
  onClick,
}: {
  icon: React.ReactNode
  label: string
  active: boolean
  onClick: () => void
}) {
  return (
    <button 
      onClick={onClick}
      className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all ${
        active 
          ? "bg-violet-500/15 text-violet-400 shadow-[inset_0_1px_1px_rgba(255,255,255,0.05)] border border-violet-500/20" 
          : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200 border border-transparent"
      }`}
    >
      <span className="opacity-80 scale-90">{icon}</span>
      <span>{label}</span>
    </button>
  )
}

function DatasetIntelligenceView({
  onOrchestrate,
  autonomyMode,
}: {
  onOrchestrate?: () => void
  autonomyMode: boolean
}) {
  return <DatasetIntelligence onOrchestrate={onOrchestrate} autonomyMode={autonomyMode} />
}

function ExperimentLabView() {
  return <ExperimentLab />
}
