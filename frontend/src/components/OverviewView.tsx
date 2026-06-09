"use client"

import { useWorkspaceStore } from "@/store/workspaceStore"
import { Database, Target, Trophy, Activity, ArrowRight, Lightbulb, ChevronDown } from "lucide-react"

export default function OverviewView() {
  const datasetIntelligence = useWorkspaceStore((state) => state.datasetIntelligence) as any
  const workflow = useWorkspaceStore((state) => state.workflow)
  const leaderboard = useWorkspaceStore((state) => state.leaderboard)
  const setActiveView = useWorkspaceStore((state) => state.setActiveView)

  if (!datasetIntelligence || !workflow || !leaderboard.length) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center min-h-[500px]">
        <h2 className="text-xl font-bold text-slate-200">No Experiment Results Yet</h2>
        <p className="text-slate-500 text-sm mt-2 mb-6">Upload a dataset and run the pipeline to see the overview.</p>
        <button 
          onClick={() => setActiveView('explore')}
          className="bg-cyan-600 hover:bg-cyan-500 text-white px-6 py-2 rounded-lg text-sm font-bold transition-colors"
        >
          Go to Explore
        </button>
      </div>
    )
  }

  const datasetName = datasetIntelligence.dataset || "Uploaded Dataset"
  const taskType = (datasetIntelligence.task_type || "Classification").replace("_", " ")
  const winningModel = leaderboard[0]
  
  // Format workflow into a nice string: KNN Imputer → SMOTE → XGBoost
  const workflowPath = workflow.steps
    .filter(s => !['load_dataset', 'evaluate_model', 'generate_report', 'shap_analysis'].includes(s.name))
    .map(s => {
      const parts = s.name.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1))
      if (s.category === 'model') return winningModel.name
      return parts.join(' ')
    })
    .join(" → ")

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 pb-20">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-semibold text-neutral-100 tracking-tight">Experiment Overview</h1>
          <div className="flex items-center gap-3 mt-2">
            <span className="flex items-center gap-1.5 text-[10px] uppercase font-bold tracking-wider text-neutral-400 bg-neutral-900 px-3 py-1 rounded border border-neutral-800">
              <Database className="w-3 h-3 text-red-500" /> {datasetName}
            </span>
            <span className="flex items-center gap-1.5 text-[10px] uppercase font-bold tracking-wider text-neutral-400 bg-neutral-900 px-3 py-1 rounded border border-neutral-800">
              <span className="w-1.5 h-1.5 rounded-full bg-red-500" /> Analysis Complete
            </span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative group">
            <button className="bg-neutral-900 hover:bg-neutral-800 text-neutral-200 px-4 py-2 rounded text-sm font-medium transition-colors border border-neutral-800 flex items-center gap-2">
              Export <ChevronDown className="w-3.5 h-3.5" />
            </button>
            <div className="absolute right-0 mt-2 w-56 bg-[#111111] border border-neutral-800 rounded shadow-xl opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
              <a 
                href="http://localhost:8000/api/export/jupyter" 
                download
                className="block px-4 py-3 text-sm text-neutral-300 hover:bg-neutral-800 hover:text-white transition-colors border-b border-neutral-800"
              >
                Jupyter Notebook (.ipynb)
              </a>
              <a 
                href="http://localhost:8000/api/export/deployment" 
                download
                className="block px-4 py-3 text-sm text-neutral-300 hover:bg-neutral-800 hover:text-white transition-colors"
              >
                1-Click Deployment (Zip)
              </a>
            </div>
          </div>
          <button 
            onClick={() => setActiveView('results')}
            className="bg-neutral-900 hover:bg-neutral-800 text-neutral-200 px-4 py-2 rounded text-sm font-medium transition-colors border border-neutral-800 flex items-center gap-2"
          >
            View Full Results <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        
        {/* Top left card: Task & Model */}
        <div className="bg-[#0A0A0A] border border-white/5 rounded-2xl p-8 flex flex-col justify-between h-44 shadow-lg relative overflow-hidden group">
          <div className="absolute inset-0 bg-gradient-to-br from-white/[0.02] to-transparent pointer-events-none" />
          <div className="relative z-10">
            <div className="text-[11px] uppercase tracking-widest font-semibold text-neutral-500 mb-1 flex items-center gap-2">
              <Target className="w-3.5 h-3.5" /> Target Task
            </div>
            <div className="text-xl font-medium text-neutral-200 capitalize">{taskType}</div>
          </div>
          
          <div className="relative z-10">
            <div className="text-[11px] uppercase tracking-widest font-semibold text-neutral-500 mb-1 flex items-center gap-2">
              <Trophy className="w-3.5 h-3.5 text-red-500" /> Winning Model
            </div>
            <div className="text-3xl font-bold text-neutral-100 group-hover:text-red-400 transition-colors duration-300">
              {winningModel.name}
            </div>
          </div>
        </div>

        {/* Top right card: Score */}
        <div className="bg-[#0A0A0A] border border-white/5 rounded-2xl p-8 flex flex-col items-center justify-center h-44 shadow-lg group cursor-pointer hover:border-red-500/30 transition-all duration-300 relative overflow-hidden" onClick={() => setActiveView('results')}>
          <div className="absolute inset-0 bg-gradient-to-br from-red-500/[0.02] to-transparent pointer-events-none group-hover:opacity-100 opacity-0 transition-opacity duration-300" />
          <div className="relative z-10 flex items-center gap-4">
            <div className="bg-red-500/10 p-3 rounded-full border border-red-500/20 group-hover:scale-110 transition-transform duration-300">
              <Activity className="w-6 h-6 text-red-500" />
            </div>
            <div className="text-6xl font-bold text-neutral-100 tracking-tighter">
              {(winningModel.score * 100).toFixed(1)}<span className="text-3xl text-neutral-500 font-medium">%</span>
            </div>
          </div>
          <div className="text-[11px] font-semibold uppercase tracking-widest text-neutral-500 mt-4 relative z-10 group-hover:text-red-400/70 transition-colors">
            Primary Metric
          </div>
        </div>

      </div>

      {/* Workflow Path */}
      <div className="bg-[#0A0A0A] border border-white/5 rounded-2xl p-6 mb-8 shadow-lg cursor-pointer hover:border-white/10 transition-all duration-300 relative overflow-hidden" onClick={() => setActiveView('pipeline')}>
        <div className="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-red-500 to-red-800" />
        <div className="text-[11px] uppercase tracking-widest font-semibold text-neutral-500 mb-4 flex items-center justify-between pl-2">
          <span>Executed Pipeline</span>
          <span className="text-red-400 hover:text-red-300 flex items-center gap-1 transition-colors">Explore Workflow <ArrowRight className="w-3 h-3" /></span>
        </div>
        <div className="font-mono text-sm text-neutral-300 flex flex-wrap items-center gap-3 pl-2">
          {workflowPath.split(' → ').map((node, i, arr) => (
            <span key={i} className="flex items-center gap-3">
              <span className={`px-4 py-2 rounded-lg border shadow-sm ${i === arr.length - 1 ? 'bg-red-500/10 border-red-500/30 text-red-400 font-bold' : 'bg-[#111111] border-white/5 text-neutral-300 hover:bg-white/[0.04] transition-colors'}`}>
                {node}
              </span>
              {i < arr.length - 1 && <span className="text-neutral-600 font-bold">→</span>}
            </span>
          ))}
        </div>
      </div>

      {/* Top Insight */}
      <div className="bg-gradient-to-r from-[#0A0A0A] to-[#111111] border border-white/5 rounded-2xl p-6 shadow-lg cursor-pointer hover:border-white/10 transition-all duration-300" onClick={() => setActiveView('results')}>
        <div className="flex items-start gap-5">
          <div className="bg-white/5 border border-white/10 p-3 rounded-xl shrink-0 shadow-inner">
            <Lightbulb className="w-6 h-6 text-yellow-500/80" />
          </div>
          <div>
            <div className="text-[11px] uppercase tracking-widest font-semibold text-neutral-500 mb-2">Top Insight</div>
            <div className="text-neutral-300 text-sm leading-relaxed max-w-4xl">
              Based on SHAP values, the <strong className="text-neutral-100">{winningModel.name}</strong> model relies heavily on specific engineered features. 
              Review the Results tab to see exact feature importance breakdowns and alternatives that were rejected.
            </div>
          </div>
        </div>
      </div>

    </div>
  )
}
