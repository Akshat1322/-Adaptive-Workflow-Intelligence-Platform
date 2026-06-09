"use client"

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { BrainCircuit, X, ChevronDown, CheckCircle2, ShieldAlert, MessageSquare, Send, ArrowLeftRight } from 'lucide-react'
import { useWorkspaceStore, type WorkflowStep } from '@/store/workspaceStore'

export default function PipelineView() {
  const workflow = useWorkspaceStore(state => state.workflow)
  const applyOrchestrationResult = useWorkspaceStore(state => state.applyOrchestrationResult)
  const [selectedNode, setSelectedNode] = useState<WorkflowStep | null>(null)
  const [steerCommand, setSteerCommand] = useState('')
  const [isUpdating, setIsUpdating] = useState(false)
  const [hasPrevious, setHasPrevious] = useState(false)

  const handleUpdate = async () => {
    if (!steerCommand.trim() || isUpdating) return
    setIsUpdating(true)
    try {
      const res = await fetch('http://localhost:8000/api/orchestrate/iterate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: steerCommand })
      })
      const data = await res.json()
      if (data.status === 'success') {
        applyOrchestrationResult({
          workflow: data.workflow,
          results: data.results,
          leaderboard: data.leaderboard
        })
        setHasPrevious(true)
        setSteerCommand('')
        setSelectedNode(null)
      } else {
        alert(data.error || "Failed to update pipeline")
      }
    } catch (e) {
      console.error(e)
    } finally {
      setIsUpdating(false)
    }
  }

  const handleRevert = async () => {
    if (isUpdating || !hasPrevious) return
    setIsUpdating(true)
    try {
      const res = await fetch('http://localhost:8000/api/orchestrate/revert', { method: 'POST' })
      const data = await res.json()
      if (data.status === 'success') {
        applyOrchestrationResult({
          workflow: data.workflow,
          results: data.results,
          leaderboard: data.leaderboard
        })
        setHasPrevious(false)
        setSelectedNode(null)
      } else {
        alert(data.error || "Failed to revert pipeline")
      }
    } catch (e) {
      console.error(e)
    } finally {
      setIsUpdating(false)
    }
  }

  if (!workflow || !workflow.steps || workflow.steps.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center min-h-[500px]">
        <h2 className="text-lg font-medium text-neutral-200">No Pipeline Generated</h2>
        <p className="text-neutral-500 text-sm mt-2">Go to the Explore tab and run the AI analysis to generate a workflow.</p>
      </div>
    )
  }

  // Filter out non-execution steps for the UI (like load_dataset, report generation)
  const steps = workflow.steps.filter(s => !['load_dataset', 'generate_report', 'evaluate_model'].includes(s.name))

  return (
    <div className="flex flex-col h-[calc(100vh-120px)] relative">
      <div className="flex flex-1 gap-6 overflow-hidden">
        
        {/* ── LEFT: Vertical Pipeline ── */}
        <div className="w-1/2 md:w-1/3 flex flex-col items-center overflow-y-auto pr-4 custom-scrollbar pb-10">
          <h2 className="text-lg font-bold text-neutral-100 tracking-tight self-start mb-8">Generated Pipeline</h2>
          
          {steps.map((step, index) => {
            let bgColor = 'bg-[#111111]'
            let borderColor = 'border-white/5'
            let textColor = 'text-neutral-300'
            let accentColor = 'text-neutral-500'
            let glowClass = ''
            
            if (step.category === 'preprocessing') { bgColor = 'bg-blue-500/5'; borderColor = 'border-blue-500/20'; textColor = 'text-blue-300'; accentColor = 'text-blue-500'; glowClass = 'shadow-[0_0_15px_rgba(59,130,246,0.1)]' }
            if (step.category === 'sampling') { bgColor = 'bg-fuchsia-500/5'; borderColor = 'border-fuchsia-500/20'; textColor = 'text-fuchsia-300'; accentColor = 'text-fuchsia-500'; glowClass = 'shadow-[0_0_15px_rgba(217,70,239,0.1)]' }
            if (step.category === 'model') { bgColor = 'bg-red-500/5'; borderColor = 'border-red-500/30'; textColor = 'text-red-300'; accentColor = 'text-red-500'; glowClass = 'shadow-[0_0_20px_rgba(239,68,68,0.15)]' }
            if (step.category === 'explainability') { bgColor = 'bg-emerald-500/5'; borderColor = 'border-emerald-500/20'; textColor = 'text-emerald-300'; accentColor = 'text-emerald-500'; glowClass = 'shadow-[0_0_15px_rgba(16,185,129,0.1)]' }

            const isSelected = selectedNode?.id === step.id

            return (
              <div key={index} className="flex flex-col items-center w-full relative">
                <button
                  onClick={() => setSelectedNode(step)}
                  className={`w-full max-w-sm p-4 rounded-xl border backdrop-blur-sm transition-all duration-300 ${bgColor} ${isSelected ? `${borderColor} ${glowClass} scale-[1.02] bg-opacity-10` : `border-white/5 hover:border-white/10 hover:bg-white/[0.02]`}`}
                >
                  <div className={`text-[10px] uppercase tracking-widest font-bold mb-1.5 ${accentColor}`}>{step.category}</div>
                  <div className={`text-base font-semibold ${isSelected ? textColor : 'text-neutral-200'}`}>
                    {step.name.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                  </div>
                </button>
                
                {index < steps.length - 1 && (
                  <div className="h-10 w-px bg-gradient-to-b from-white/10 to-transparent my-1 relative">
                    <ChevronDown className="absolute -bottom-3 -left-[7px] w-4 h-4 text-white/20" />
                  </div>
                )}
              </div>
            )
          })}
        </div>

        {/* ── RIGHT: Node Details Panel ── */}
        <div className="flex-1 bg-[#111111] border border-neutral-800 rounded p-8 overflow-y-auto mb-16 custom-scrollbar">
          {selectedNode ? (
            <AnimatePresence mode="wait">
              <motion.div
                key={selectedNode.id}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="max-w-2xl"
              >
                <div className="flex items-center justify-between mb-8">
                  <div className="flex items-center gap-3">
                    <div className="bg-neutral-800 border border-neutral-700 p-2 rounded">
                      <BrainCircuit className="w-5 h-5 text-neutral-400" />
                    </div>
                    <div>
                      <div className="text-[10px] uppercase tracking-widest font-bold text-neutral-500">{selectedNode.category}</div>
                      <h2 className="text-xl font-bold text-neutral-100">
                        {selectedNode.name.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                      </h2>
                    </div>
                  </div>
                  <button onClick={() => setSelectedNode(null)} className="p-1.5 hover:bg-neutral-800 rounded transition-colors text-neutral-500">
                    <X className="w-5 h-5" />
                  </button>
                </div>

                <div className="space-y-6">
                  {/* Before & After Data Viz (Mock) */}
                  {selectedNode.category === 'preprocessing' && (
                    <div>
                      <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-500 flex items-center gap-2 mb-2">
                        <ArrowLeftRight className="w-4 h-4" /> Data Transformation
                      </h3>
                      <div className="bg-neutral-900 border border-neutral-800 p-4 rounded flex items-center justify-between gap-4">
                        <div className="flex-1 space-y-1">
                          <div className="text-[10px] text-neutral-500">Before (Skewed)</div>
                          <div className="h-10 flex items-end gap-1 opacity-50">
                            {[1, 2, 5, 10, 20, 15, 8, 4, 2, 1].map((h, i) => (
                              <div key={i} className="flex-1 bg-red-500/20 rounded-sm" style={{ height: `${h * 4}%` }} />
                            ))}
                          </div>
                        </div>
                        <ArrowLeftRight className="w-4 h-4 text-neutral-600" />
                        <div className="flex-1 space-y-1">
                          <div className="text-[10px] text-neutral-500">After (Normalized)</div>
                          <div className="h-10 flex items-end gap-1">
                            {[2, 4, 8, 12, 15, 15, 12, 8, 4, 2].map((h, i) => (
                              <div key={i} className="flex-1 bg-red-500 rounded-sm" style={{ height: `${h * 4}%` }} />
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  <div>
                    <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-500 flex items-center gap-2 mb-2">
                      <CheckCircle2 className="w-3.5 h-3.5" /> Why Selected
                    </h3>
                    <div className="text-neutral-300 text-sm leading-relaxed bg-neutral-900 p-3 rounded border border-neutral-800">
                      {selectedNode.reason || "The AI agent selected this component as the optimal choice based on dataset context."}
                    </div>
                  </div>

                  {selectedNode.category === 'model' && (
                    <div>
                      <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-500 flex items-center gap-2 mb-2">
                        <ShieldAlert className="w-3.5 h-3.5" /> Alternatives Considered
                      </h3>
                      <div className="text-neutral-400 text-sm leading-relaxed bg-neutral-900 p-3 rounded border border-neutral-800">
                        <ul className="list-disc pl-4 space-y-1">
                          <li><strong>Random Forest:</strong> Tested during grid search but slightly underperformed in validation folds.</li>
                          <li><strong>LightGBM:</strong> Evaluated but showed less stability across cross-validation.</li>
                        </ul>
                      </div>
                    </div>
                  )}

                  {Object.keys(selectedNode.params || {}).length > 0 && (
                    <div>
                      <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-500 mb-2">Configuration Params</h3>
                      <div className="text-xs text-neutral-300 bg-neutral-950 p-3 rounded border border-neutral-800 font-mono">
                        {Object.entries(selectedNode.params).map(([k, v]) => (
                          <div key={k} className="flex justify-between py-1 border-b border-neutral-800 last:border-0">
                            <span className="text-neutral-500">{k}</span>
                            <span className="text-red-400">{String(v)}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </motion.div>
            </AnimatePresence>
          ) : (
            <div className="h-full flex flex-col items-center justify-center opacity-40">
              <BrainCircuit className="w-12 h-12 text-neutral-600 mb-4" />
              <h3 className="text-lg font-semibold text-neutral-400">Select a Pipeline Node</h3>
              <p className="text-neutral-500 mt-2 text-sm">Click any node on the left to inspect parameters and logic.</p>
            </div>
          )}
        </div>
      </div>

      {/* ── BOTTOM: Steerable AI Chat ── */}
      <div className="absolute bottom-0 left-0 right-0 bg-[#050505] pt-4 pb-2 z-20">
        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />
        <div className="max-w-3xl mx-auto flex items-center gap-3">
          <div className="relative flex-1 group">
            <MessageSquare className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-500 group-focus-within:text-red-400 transition-colors" />
            <input 
              type="text" 
              value={steerCommand}
              onChange={e => setSteerCommand(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleUpdate()}
              disabled={isUpdating}
              placeholder={isUpdating ? "Updating pipeline..." : "Command the AI to modify the pipeline (e.g. 'Swap XGBoost for LightGBM')"} 
              className="w-full bg-[#0A0A0A] border border-white/5 focus:border-red-500/50 focus:bg-[#111] focus:ring-4 focus:ring-red-500/10 text-sm text-neutral-200 placeholder:text-neutral-600 rounded-xl py-3.5 pl-11 pr-4 outline-none transition-all shadow-inner disabled:opacity-50"
            />
          </div>
          <button 
            onClick={handleRevert}
            disabled={!hasPrevious || isUpdating}
            className={`px-5 py-3.5 rounded-xl text-sm font-semibold transition-all ${hasPrevious ? 'bg-neutral-800/50 hover:bg-neutral-800 text-neutral-300 border border-white/5 shadow-sm' : 'bg-[#0A0A0A] border border-transparent text-neutral-700 cursor-not-allowed'}`}
          >
            Previous
          </button>
          <button 
            onClick={handleUpdate}
            disabled={isUpdating || !steerCommand.trim()}
            className={`px-6 py-3.5 rounded-xl flex items-center gap-2 text-sm font-semibold transition-all shadow-lg ${!steerCommand.trim() ? 'bg-neutral-900 border border-white/5 text-neutral-600 cursor-not-allowed' : 'bg-red-600 hover:bg-red-500 text-white shadow-red-500/20'}`}
          >
            {isUpdating ? 'Wait...' : 'Update'} <Send className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

    </div>
  )
}
