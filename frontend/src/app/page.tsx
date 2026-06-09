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
    <div className="flex flex-col md:flex-row h-screen w-full bg-[#030303] text-neutral-200 font-sans overflow-hidden selection:bg-red-500/30">
      
      {/* ── LEFT PANEL: Navigation ── */}
      <aside className="w-full md:w-[260px] h-auto md:h-full flex flex-row md:flex-col items-center md:items-stretch bg-[#0A0A0A] border-b md:border-r md:border-b-0 border-neutral-800/60 p-2 md:p-5 shrink-0 shadow-2xl z-20">
        <div className="flex items-center gap-2 md:gap-3 md:mb-10 px-2 shrink-0 mr-4 md:mr-0">
          <div className="bg-gradient-to-br from-red-500 to-red-700 p-2 rounded-lg flex items-center justify-center shadow-[0_0_15px_rgba(225,29,72,0.3)]">
            <Database className="w-4 h-4 text-white" />
          </div>
          <span className="font-bold text-xl tracking-tight text-neutral-100 hidden md:block">AWIP</span>
        </div>

        <div className="hidden md:block mb-3 px-3 text-[11px] uppercase tracking-widest font-semibold text-neutral-500">
          Workspace
        </div>

        <nav className="flex flex-row md:flex-col flex-1 gap-1 md:gap-0 md:space-y-1.5 overflow-x-auto hide-scrollbar items-center md:items-stretch">
          <NavItem 
            icon={<LayoutDashboard className="w-4 h-4 md:w-5 md:h-5" />} 
            label="Overview" 
            active={activeView === "overview"} 
            onClick={() => setActiveView("overview")}
            disabled={!datasetIntelligence || isOrchestrating}
          />
          <NavItem 
            icon={<Database className="w-4 h-4 md:w-5 md:h-5" />} 
            label="Explore Dataset" 
            active={activeView === "explore"} 
            onClick={() => setActiveView("explore")} 
          />
          <NavItem 
            icon={<Activity className="w-4 h-4 md:w-5 md:h-5" />} 
            label="Pipeline" 
            active={activeView === "pipeline"} 
            onClick={() => setActiveView("pipeline")}
            disabled={!useWorkspaceStore.getState().workflow}
          />
          <NavItem 
            icon={<Beaker className="w-4 h-4 md:w-5 md:h-5" />} 
            label="Results" 
            active={activeView === "results"} 
            onClick={() => setActiveView("results")}
            disabled={!useWorkspaceStore.getState().workflow}
          />
          <NavItem 
            icon={<Code2 className="w-4 h-4 md:w-5 md:h-5" />} 
            label="Code & Reasoning" 
            active={activeView === "reasoning"} 
            onClick={() => setActiveView("reasoning")}
            disabled={!datasetIntelligence}
          />
        </nav>
      </aside>

      {/* ── MAIN CONTENT AREA ── */}
      <main className="flex-1 flex flex-col h-full bg-[#050505] relative overflow-hidden">
        {/* Subtle grid background */}
        <div className="absolute inset-0 bg-[url('https://grainy-gradients.vercel.app/noise.svg')] opacity-20 pointer-events-none mix-blend-overlay"></div>
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:64px_64px] pointer-events-none opacity-50"></div>
        
        <div className="flex-1 overflow-y-auto p-4 md:p-10 z-10 custom-scrollbar">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeView}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -10 }}
              transition={{ duration: 0.2 }}
              className="h-full w-full max-w-7xl mx-auto"
            >
              {activeView === "explore" && <ExploreView />}
              {activeView === "pipeline" && <PipelineView />}
              {activeView === "results" && <ResultsView />}
              {activeView === "reasoning" && <ReasoningView />}
              {activeView === "overview" && <OverviewView />}
            </motion.div>
          </AnimatePresence>
        </div>
      </main>

      <ToastContainer />

      {/* Global CSS for hidden scrollbar on mobile nav */}
      <style dangerouslySetInnerHTML={{__html: `
        .hide-scrollbar::-webkit-scrollbar {
          display: none;
        }
        .hide-scrollbar {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }
      `}} />
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
      className={`w-auto md:w-full shrink-0 flex items-center gap-2 md:gap-3 px-3 md:px-3 py-2 md:py-2.5 rounded-lg text-[13px] md:text-sm font-medium transition-all duration-200 group relative overflow-hidden ${
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
          className="absolute left-0 bottom-0 md:top-1/4 md:bottom-1/4 h-1 w-full md:w-1 md:h-auto bg-red-500 rounded-t-sm md:rounded-t-none md:rounded-r-full shadow-[0_0_8px_rgba(239,68,68,0.5)]" 
        />
      )}
      <span className={`opacity-80 transition-colors ${active ? "text-red-400" : "group-hover:text-neutral-300"}`}>{icon}</span>
      <span className="whitespace-nowrap">{label}</span>
    </button>
  )
}
