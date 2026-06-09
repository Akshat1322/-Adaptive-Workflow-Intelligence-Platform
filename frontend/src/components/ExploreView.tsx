"use client"

import { useState, useRef } from "react"
import { UploadCloud, CheckCircle2, ChevronRight, Fingerprint, Activity, Database, AlertTriangle, Target, LayoutList, Check } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import { useWorkspaceStore } from "@/store/workspaceStore"
import { apiFetch, showSuccess } from "@/lib/api"
import { runWorkspaceOrchestration } from "@/lib/orchestration"

export default function ExploreView() {
  const datasetIntelligence = useWorkspaceStore((state) => state.datasetIntelligence) as any
  const isUploading = useWorkspaceStore((state) => state.isUploading)
  const isOrchestrating = useWorkspaceStore((state) => state.isOrchestrating)
  const setDatasetIntelligence = useWorkspaceStore((state) => state.setDatasetIntelligence)
  const setIsUploading = useWorkspaceStore((state) => state.setIsUploading)
  const agentMessages = useWorkspaceStore((state) => state.agentMessages)

  const [selectedTarget, setSelectedTarget] = useState<string | null>(null)
  const [expandedCol, setExpandedCol] = useState<string | null>(null)
  const streamCleanupRef = useRef<(() => void) | null>(null)

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    setIsUploading(true)
    const formData = new FormData()
    formData.append("file", file)

    try {
      const res = await apiFetch("/api/upload", { method: "POST", body: formData })
      const data = await res.json()
      setDatasetIntelligence(data)
      // Auto-select top candidate if available
      if (data.target_candidates && data.target_candidates.length > 0) {
        setSelectedTarget(data.target_candidates[0].name)
      }
      showSuccess(`Dataset "${file.name}" analyzed successfully`)
    } catch {
      // toast handled
    } finally {
      setIsUploading(false)
    }
  }

  const handleOrchestrate = () => {
    if (isOrchestrating || !selectedTarget) return

    streamCleanupRef.current?.()
    streamCleanupRef.current = runWorkspaceOrchestration({
      targetCol: selectedTarget,
      onComplete: () => {
        streamCleanupRef.current = null
      },
    })
  }

  if (isUploading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center min-h-[500px]">
        <div className="w-10 h-10 border-2 border-neutral-800 border-t-red-500 rounded-full animate-spin mb-6" />
        <h2 className="text-lg font-medium text-neutral-200">Analyzing Dataset Context...</h2>
        <p className="text-neutral-500 text-sm mt-2">Extracting signals and intelligence.</p>
      </div>
    )
  }

  if (isOrchestrating) {
    return <TaskCentricLoading messages={agentMessages} />
  }

  if (!datasetIntelligence) {
    return (
      <div className="flex-1 border-2 border-dashed border-white/10 hover:border-red-500/30 transition-colors rounded-3xl flex items-center justify-center bg-[#111111] min-h-[500px] group cursor-pointer relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-red-500/[0.02] to-transparent pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
        <input
          type="file"
          accept=".csv"
          className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
          onChange={handleFileUpload}
        />
        <div className="text-center relative z-0">
          <div className="w-24 h-24 rounded-full bg-[#0A0A0A] border border-white/5 flex items-center justify-center mx-auto mb-8 shadow-[0_0_30px_rgba(225,29,72,0.1)] group-hover:shadow-[0_0_40px_rgba(225,29,72,0.2)] transition-all duration-500 group-hover:scale-105">
            <UploadCloud className="w-10 h-10 text-neutral-500 group-hover:text-red-500 transition-colors" />
          </div>
          <h1 className="text-3xl font-bold text-neutral-100 tracking-tight mb-3">AWIP Workspace</h1>
          <p className="text-neutral-500 text-sm max-w-sm mx-auto leading-relaxed">
            Upload a dataset to begin the automated analysis and pipeline design process.
          </p>
          <div className="mt-8 inline-flex items-center gap-2 bg-red-600 hover:bg-red-500 text-white px-8 py-3 rounded-full text-sm font-semibold transition-colors shadow-[0_0_20px_rgba(220,38,38,0.2)]">
            Upload Dataset
          </div>
        </div>
      </div>
    )
  }

  const { rows, cols, quality_score, intelligence_findings, target_candidates, column_details } = datasetIntelligence
  const totalMissing = column_details?.reduce((acc: number, c: any) => acc + (c.missing_pct > 0 ? 1 : 0), 0) || 0

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 pb-20">
      
      {/* ── TOP SUMMARY CARDS ── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <MetricCard icon={<LayoutList />} label="Rows" value={Number(rows).toLocaleString()} />
        <MetricCard icon={<Database />} label="Columns" value={String(cols)} />
        <MetricCard icon={<AlertTriangle />} label="Missing Data" value={`${totalMissing} cols`} />
        <MetricCard icon={<Activity />} label="Quality Score" value={`${Math.round(Number(quality_score))}%`} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* ── SUGGESTED TARGETS ── */}
        <div className="lg:col-span-1 bg-[#0A0A0A] border border-white/5 rounded-2xl p-8 shadow-lg relative overflow-hidden group">
          <div className="absolute top-0 right-0 w-32 h-32 bg-red-500/5 rounded-full blur-2xl -mt-16 -mr-16 pointer-events-none" />
          <h3 className="text-sm font-semibold text-neutral-100 flex items-center gap-2 mb-2 relative z-10">
            <Target className="w-4 h-4 text-red-500" /> Suggested Targets
          </h3>
          <p className="text-[11px] uppercase tracking-widest font-semibold text-neutral-500 mb-6 relative z-10">Select the column you want to predict.</p>
          <div className="space-y-3 relative z-10">
            {target_candidates?.map((c: any, i: number) => (
              <button
                key={c.name}
                onClick={() => setSelectedTarget(c.name)}
                className={`w-full flex items-center justify-between p-3 rounded-xl border text-sm transition-all duration-300 ${
                  selectedTarget === c.name 
                    ? "bg-red-500/10 border-red-500/30 text-red-400 shadow-[0_0_15px_rgba(239,68,68,0.1)]" 
                    : "bg-[#111111] border-white/5 text-neutral-300 hover:border-white/10 hover:bg-white/[0.02]"
                }`}
              >
                <div className="flex items-center gap-3">
                  <span className="font-semibold">{c.name}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-[10px] opacity-60 font-mono">({c.confidence}%)</span>
                  {selectedTarget === c.name && <CheckCircle2 className="w-4 h-4 text-red-500" />}
                </div>
              </button>
            ))}
            {(!target_candidates || target_candidates.length === 0) && (
              <div className="text-xs text-neutral-500">No candidates found.</div>
            )}
          </div>
          
          <button
            onClick={handleOrchestrate}
            disabled={!selectedTarget || isOrchestrating}
            className="w-full mt-8 bg-red-600 hover:bg-red-500 disabled:opacity-50 disabled:hover:bg-red-600 text-white py-3 rounded-xl text-sm font-semibold transition-all shadow-[0_0_20px_rgba(220,38,38,0.2)] active:scale-[0.98] relative z-10"
          >
            Run Pipeline
          </button>
        </div>

        {/* ── AI INTELLIGENCE FINDINGS ── */}
        <div className="lg:col-span-2 bg-[#0A0A0A] border border-white/5 rounded-2xl p-8 shadow-lg">
          <h3 className="text-sm font-semibold text-neutral-100 flex items-center gap-2 mb-6">
            <Fingerprint className="w-4 h-4 text-red-500" /> Intelligence Findings
          </h3>
          <ul className="space-y-4">
            {intelligence_findings?.map((finding: string, i: number) => (
              <li key={i} className="flex items-start gap-4">
                <div className="mt-1 w-1.5 h-1.5 rounded-full bg-red-500 shrink-0 shadow-[0_0_8px_rgba(239,68,68,0.8)]" />
                <span className="text-neutral-300 text-sm leading-relaxed">{finding}</span>
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* ── DATASET PREVIEW (COLUMNS) ── */}
      <div>
        <h3 className="text-xl font-bold text-neutral-100 mb-6 px-1 tracking-tight">Dataset Explorer</h3>
        <div className="bg-[#0A0A0A] border border-white/5 rounded-2xl overflow-hidden shadow-lg">
          <div className="grid grid-cols-12 gap-4 p-5 border-b border-white/5 bg-white/[0.02] text-[11px] font-bold text-neutral-500 uppercase tracking-widest">
            <div className="col-span-5">Name</div>
            <div className="col-span-3">Type</div>
            <div className="col-span-2">Missing</div>
            <div className="col-span-2">Unique</div>
          </div>
          <div className="divide-y divide-white/5 max-h-[600px] overflow-y-auto custom-scrollbar">
            {column_details?.map((col: any) => (
              <div key={col.name} className="flex flex-col">
                <div 
                  className="grid grid-cols-12 gap-4 p-5 items-center hover:bg-white/[0.02] transition-colors cursor-pointer group"
                  onClick={() => setExpandedCol(expandedCol === col.name ? null : col.name)}
                >
                  <div className="col-span-5 font-mono text-sm text-neutral-200 flex items-center gap-3">
                    <ChevronRight className={`w-4 h-4 text-neutral-600 transition-transform duration-300 ${expandedCol === col.name ? "rotate-90 text-red-500" : "group-hover:text-neutral-400"}`} />
                    <span className="font-medium group-hover:text-neutral-100 transition-colors">{col.name}</span>
                    {selectedTarget === col.name && <span className="text-[10px] bg-red-500/10 border border-red-500/20 text-red-400 px-2 py-0.5 rounded-full ml-2 font-sans font-bold">TARGET</span>}
                  </div>
                  <div className="col-span-3">
                    <span className={`text-[11px] font-semibold px-2.5 py-1 rounded-md bg-[#111111] border ${
                      col.type === "Numeric" ? "text-blue-400 border-blue-500/20" : 
                      col.type === "Categorical" ? "text-fuchsia-400 border-fuchsia-500/20" : 
                      "text-neutral-400 border-white/10"
                    }`}>
                      {col.type}
                    </span>
                  </div>
                  <div className="col-span-2 text-sm text-neutral-400 font-mono">
                    <span className={col.missing_pct > 0 ? "text-red-400 font-bold" : ""}>{col.missing_pct}%</span>
                  </div>
                  <div className="col-span-2 text-sm text-neutral-400 font-mono">{col.unique_count}</div>
                </div>
                
                {/* Expanded Details */}
                <AnimatePresence>
                  {expandedCol === col.name && (
                    <motion.div 
                      initial={{ height: 0, opacity: 0 }} 
                      animate={{ height: "auto", opacity: 1 }} 
                      exit={{ height: 0, opacity: 0 }}
                      className="overflow-hidden bg-[#111111] border-t border-white/5"
                    >
                      <div className="p-6 ml-8">
                        {col.type === "Numeric" && col.metrics ? (
                          <div className="grid grid-cols-3 gap-5 max-w-lg">
                            <div className="bg-[#0A0A0A] p-4 rounded-xl border border-white/5 shadow-inner">
                              <div className="text-[11px] text-neutral-500 uppercase tracking-widest font-semibold mb-2">Min</div>
                              <div className="font-mono text-base text-neutral-200">{Number(col.metrics.min).toFixed(2)}</div>
                            </div>
                            <div className="bg-[#0A0A0A] p-4 rounded-xl border border-white/5 shadow-inner">
                              <div className="text-[11px] text-neutral-500 uppercase tracking-widest font-semibold mb-2">Max</div>
                              <div className="font-mono text-base text-neutral-200">{Number(col.metrics.max).toFixed(2)}</div>
                            </div>
                            <div className="bg-[#0A0A0A] p-4 rounded-xl border border-white/5 shadow-inner">
                              <div className="text-[11px] text-neutral-500 uppercase tracking-widest font-semibold mb-2">Mean</div>
                              <div className="font-mono text-base text-neutral-200">{Number(col.metrics.mean).toFixed(2)}</div>
                            </div>
                          </div>
                        ) : col.type === "Categorical" && col.metrics?.categories ? (
                          <div className="bg-[#0A0A0A] p-5 rounded-xl border border-white/5 shadow-inner max-w-2xl">
                            <div className="text-[11px] text-neutral-500 uppercase tracking-widest font-semibold mb-3">Sample Categories</div>
                            <div className="flex flex-wrap gap-2.5">
                              {col.metrics.categories.map((c: string, i: number) => (
                                <span key={i} className="text-xs font-medium bg-[#111111] text-neutral-300 px-3 py-1.5 rounded-lg border border-white/5 shadow-sm">
                                  {String(c)}
                                </span>
                              ))}
                              {col.unique_count > 5 && <span className="text-xs font-semibold text-neutral-500 px-2 py-1.5">+{col.unique_count - 5} more</span>}
                            </div>
                          </div>
                        ) : (
                          <div className="text-sm text-neutral-500 italic">No additional metrics available for this data type.</div>
                        )}
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

function MetricCard({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="bg-[#111111] border border-white/5 rounded-2xl p-5 flex flex-col justify-between h-28 shadow-md relative overflow-hidden">
      <div className="absolute top-0 right-0 w-24 h-24 bg-white/[0.02] rounded-full blur-xl -translate-y-1/2 translate-x-1/2" />
      <div className="flex justify-between items-start relative z-10">
        <div className="text-[11px] uppercase tracking-widest font-semibold text-neutral-500">{label}</div>
        <div className="text-red-500/80 scale-90 origin-top-right">{icon}</div>
      </div>
      <div className="text-3xl font-mono text-neutral-100 font-bold tracking-tight relative z-10">{value}</div>
    </div>
  )
}

// Map agent messages to a task-centric progress view
function TaskCentricLoading({ messages }: { messages: any[] }) {
  const tasks = [
    { key: "Data Agent", label: "Analyzing Dataset" },
    { key: "Feature Agent", label: "Generating Workflow" },
    { key: "Model Agent", label: "Training Models" },
    { key: "Evaluation Agent", label: "Evaluating Performance" },
    { key: "Explainability Agent", label: "Generating Explanations" },
    { key: "Reporting Agent", label: "Compiling Insights" },
  ]

  // A task is 'active' if it's the last recognized sender seen, or if it's the first task and no recognized sender has spoken
  const recognizedSenders = messages.map(m => m.sender).filter(s => tasks.some(t => t.key === s))
  const seenSenders = new Set(recognizedSenders)
  const lastRecognizedSender = recognizedSenders.length > 0 ? recognizedSenders[recognizedSenders.length - 1] : tasks[0].key

  return (
    <div className="flex-1 flex flex-col items-center justify-center min-h-[500px]">
      <div className="max-w-md w-full bg-[#0A0A0A] border border-white/5 rounded-2xl p-10 shadow-xl relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-red-500/[0.02] to-transparent pointer-events-none" />
        <h2 className="text-lg font-bold text-neutral-100 mb-8 flex items-center gap-4 relative z-10 tracking-tight">
          <div className="w-4 h-4 border-2 border-white/10 border-t-red-500 rounded-full animate-spin" />
          Running Pipeline...
        </h2>
        
        <div className="space-y-6 relative z-10">
          {tasks.map((task, i) => {
            const isActive = lastRecognizedSender === task.key
            const isComplete = seenSenders.has(task.key) && !isActive
            const isPending = !seenSenders.has(task.key) && !isActive

            return (
              <div key={task.key} className={`flex items-start gap-4 transition-opacity duration-300 ${isPending ? 'opacity-30' : 'opacity-100'}`}>
                <div className="mt-0.5">
                  {isComplete ? (
                    <CheckCircle2 className="w-5 h-5 text-red-500" />
                  ) : isActive ? (
                    <div className="w-5 h-5 border-2 border-white/10 border-t-red-500 rounded-full animate-spin" />
                  ) : (
                    <div className="w-5 h-5 border-2 border-white/5 rounded-full" />
                  )}
                </div>
                <div>
                  <div className={`font-semibold text-sm ${isActive ? 'text-neutral-100' : isComplete ? 'text-neutral-300' : 'text-neutral-500'}`}>
                    {task.label}
                  </div>
                  {(isActive || isComplete) && (
                    <div className="text-[11px] text-neutral-400 mt-1.5 font-mono bg-[#111111] border border-white/5 px-2.5 py-1.5 rounded-md inline-block max-w-[300px] truncate">
                      {messages.slice().reverse().find(m => m.sender === task.key)?.content || "Initializing agents..."}
                    </div>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
