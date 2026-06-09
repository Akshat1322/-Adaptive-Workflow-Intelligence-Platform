"use client"

import { useEffect } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Database, Activity, Beaker, Brain, Settings, LayoutDashboard, Code2 } from "lucide-react"
import { useWorkspaceStore } from "@/store/workspaceStore"

// Import views (we will create these next)
import ExploreView from "@/components/ExploreView"
import PipelineView from "@/components/PipelineView"
import ResultsView from "@/components/ResultsView"
import ReasoningView from "@/components/ReasoningView"
import OverviewView from "@/components/OverviewView"
import { ToastContainer } from "@/components/ToastContainer"

export default function WorkspacePage() {
  const activeView = useWorkspaceStore((state) => state.activeView)
  const setActiveView = useWorkspaceStore((state) => state.setActiveView)
  const datasetIntelligence = useWorkspaceStore((state) => state.datasetIntelligence)
  const isOrchestrating = useWorkspaceStore((state) => state.isOrchestrating)

  // Auto-switch to overview when orchestration finishes
  useEffect(() => {
    if (datasetIntelligence && !isOrchestrating && activeView === 'explore' && useWorkspaceStore.getState().workflow) {
       setActiveView('overview')
    }
  }, [isOrchestrating, datasetIntelligence, activeView, setActiveView])

  return (
    <div className="flex h-screen w-full bg-[#030303] text-neutral-200 font-sans overflow-hidden selection:bg-red-500/30">
      
      {/* ── LEFT PANEL: Navigation ── */}
      <aside className="w-[260px] flex flex-col bg-[#0A0A0A] border-r border-neutral-800/60 p-5 shrink-0 shadow-2xl z-10">
        <div className="flex items-center gap-3 mb-10 px-2 mt-2">
          <div className="bg-gradient-to-br from-red-500 to-red-700 p-2 rounded-lg flex items-center justify-center shadow-[0_0_15px_rgba(225,29,72,0.3)]">
            <Database className="w-4 h-4 text-white" />
          </div>
          <span className="font-bold text-xl tracking-tight text-neutral-100">AWIP</span>
        </div>

        <div className="mb-3 px-3 text-[11px] uppercase tracking-widest font-semibold text-neutral-500">
          Workspace
        </div>

        <nav className="flex-1 space-y-1.5">
          <NavItem 
            icon={<LayoutDashboard />} 
            label="Overview" 
            active={activeView === "overview"} 
            onClick={() => setActiveView("overview")}
            disabled={!datasetIntelligence || isOrchestrating}
          />
          <NavItem 
            icon={<Database />} 
            label="Explore Dataset" 
            active={activeView === "explore"} 
            onClick={() => setActiveView("explore")} 
          />
          <NavItem 
            icon={<Activity />} 
            label="Pipeline" 
            active={activeView === "pipeline"} 
            onClick={() => setActiveView("pipeline")}
            disabled={!datasetIntelligence || isOrchestrating}
          />
          <NavItem 
            icon={<Beaker />} 
            label="Results" 
            active={activeView === "results"} 
            onClick={() => setActiveView("results")}
            disabled={!datasetIntelligence || isOrchestrating}
          />
          <NavItem 
            icon={<Code2 />} 
            label="Code & Reasoning" 
            active={activeView === "reasoning"} 
            onClick={() => setActiveView("reasoning")}
            disabled={!datasetIntelligence || isOrchestrating}
          />
        </nav>

        <div className="mt-auto pt-4 border-t border-neutral-800/60">
          <NavItem 
            icon={<Settings />} 
            label="Settings" 
            active={false} 
            onClick={() => {}} 
          />
        </div>
      </aside>

      {/* ── MAIN PANEL: Workspace ── */}
      <main className="flex-1 flex flex-col relative overflow-hidden bg-[#050505]">
        {/* Subtle top gradient for depth */}
        <div className="absolute top-0 left-0 right-0 h-32 bg-gradient-to-b from-white/[0.02] to-transparent pointer-events-none" />
        
        <div className="flex-1 overflow-y-auto p-10 relative">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeView}
              initial={{ opacity: 0, y: 15 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -15 }}
              transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
              className="h-full max-w-6xl mx-auto"
            >
              {activeView === "overview" && <OverviewView />}
              {activeView === "explore" && <ExploreView />}
              {activeView === "pipeline" && <PipelineView />}
              {activeView === "results" && <ResultsView />}
              {activeView === "reasoning" && <ReasoningView />}
            </motion.div>
          </AnimatePresence>
        </div>
      </main>

      <ToastContainer />
    </div>
  )
}

function NavItem({
  icon,
  label,
  active,
  disabled = false,
  onClick,
}: {
  icon: React.ReactNode
  label: string
  active: boolean
  disabled?: boolean
  onClick: () => void
}) {
  return (
    <button 
      onClick={onClick}
      disabled={disabled}
      className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 group relative overflow-hidden ${
        active 
          ? "text-neutral-100 bg-white/[0.06] shadow-sm" 
          : disabled
            ? "text-neutral-600 cursor-not-allowed"
            : "text-neutral-400 hover:bg-white/[0.03] hover:text-neutral-200"
      }`}
    >
      {active && (
        <motion.div 
          layoutId="activeNavIndicator"
          className="absolute left-0 top-1/4 bottom-1/4 w-1 bg-red-500 rounded-r-full shadow-[0_0_8px_rgba(239,68,68,0.5)]" 
        />
      )}
      <span className={`opacity-80 scale-90 transition-colors ${active ? "text-red-400" : "group-hover:text-neutral-300"}`}>{icon}</span>
      <span>{label}</span>
    </button>
  )
}
