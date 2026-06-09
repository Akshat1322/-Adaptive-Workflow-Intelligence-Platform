"use client"

import { useRef } from "react"
import { Database, UploadCloud, LayoutList, Fingerprint, ShieldAlert, Target } from "lucide-react"
import { motion } from "framer-motion"
import { useWorkspaceStore } from "@/store/workspaceStore"
import { apiFetch, showSuccess } from "@/lib/api"
import { runWorkspaceOrchestration } from "@/lib/orchestration"
import { DatasetIntelligenceSkeleton } from "@/components/Skeleton"

export default function DatasetIntelligence({
  onOrchestrate,
  autonomyMode = false,
}: {
  onOrchestrate?: () => void
  autonomyMode?: boolean
}) {
  const streamCleanupRef = useRef<(() => void) | null>(null)
  const intelligence = useWorkspaceStore((state) => state.datasetIntelligence)
  const isUploading = useWorkspaceStore((state) => state.isUploading)
  const isOrchestrating = useWorkspaceStore((state) => state.isOrchestrating)
  const setDatasetIntelligence = useWorkspaceStore((state) => state.setDatasetIntelligence)
  const setIsUploading = useWorkspaceStore((state) => state.setIsUploading)

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
      showSuccess(`Dataset "${file.name}" analyzed successfully`)
      if (autonomyMode) {
        setTimeout(() => handleOrchestrate(), 0)
      }
    } catch {
      // toast shown by apiFetch
    } finally {
      setIsUploading(false)
    }
  }

  const handleOrchestrate = () => {
    if (isOrchestrating) return

    streamCleanupRef.current?.()
    streamCleanupRef.current = runWorkspaceOrchestration({
      onStarted: onOrchestrate,
      onComplete: () => {
        streamCleanupRef.current = null
      },
    })
  }

  if (isUploading) {
    return <DatasetIntelligenceSkeleton />
  }

  if (!intelligence) {
    return (
      <div className="flex-1 border-2 border-dashed border-slate-700/50 hover:border-cyan-500/50 transition-colors rounded-3xl flex items-center justify-center bg-slate-900/40 min-h-[400px]">
        <div className="text-center relative">
          <input
            type="file"
            accept=".csv"
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            onChange={handleFileUpload}
          />
          <div className="w-20 h-20 rounded-full bg-slate-800 flex items-center justify-center mx-auto mb-6 shadow-xl shadow-cyan-900/20">
            <UploadCloud className="w-10 h-10 text-cyan-400" />
          </div>
          <h3 className="text-xl font-bold text-slate-200 mb-2">Initialize Workspace</h3>
          <p className="text-slate-500 text-sm max-w-md mx-auto">
            Upload a CSV dataset to activate the AI Data Science Team. The Context Engine will immediately extract structural intelligence.
          </p>
          <div className="mt-6 inline-flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-300 px-6 py-2.5 rounded-full text-sm font-medium transition-colors">
            Browse Files
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-2xl font-bold text-slate-100 flex items-center gap-3">
            <Fingerprint className="text-violet-400 w-6 h-6" />
            Dataset Intelligence
          </h2>
          <p className="text-slate-400 text-sm mt-1">{String(intelligence.dataset ?? "")}</p>
        </div>
        <div className="bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          Extraction Complete
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard icon={<LayoutList />} label="Rows" value={Number(intelligence.rows ?? 0).toLocaleString()} color="cyan" />
        <MetricCard icon={<Database />} label="Columns" value={String(intelligence.cols ?? "0")} color="violet" />
        <MetricCard icon={<Target />} label="Task Inference" value={String(intelligence.task_type ?? "unknown").replace("_", " ").toUpperCase()} color="amber" />
        <MetricCard icon={<ShieldAlert />} label="Quality Score" value="92%" color="emerald" />
      </div>

      <div className="mt-8 bg-slate-900/60 border border-slate-800 rounded-2xl p-6">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-lg font-semibold text-slate-200">Recommended Action</h3>
          <button
            onClick={handleOrchestrate}
            disabled={isOrchestrating}
            className="bg-gradient-to-r from-cyan-600 to-violet-600 hover:from-cyan-500 hover:to-violet-500 disabled:opacity-60 text-white px-6 py-2 rounded-xl text-sm font-bold shadow-lg shadow-violet-900/20 transition-all active:scale-95 flex items-center gap-2"
          >
            {isOrchestrating ? (
              <>
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Orchestrating...
              </>
            ) : (
              "Orchestrate Pipeline"
            )}
          </button>
        </div>
        <p className="text-slate-400 text-sm">
          The Data Agent suggests executing the default workflow pipeline. Watch the AI Copilot panel for live agent reasoning.
        </p>
      </div>
    </div>
  )
}

function MetricCard({ icon, label, value, color }: { icon: React.ReactNode; label: string; value: string; color: string }) {
  const colorMap: Record<string, string> = {
    cyan: "text-cyan-400 bg-cyan-500/10 border-cyan-500/20",
    violet: "text-violet-400 bg-violet-500/10 border-violet-500/20",
    amber: "text-amber-400 bg-amber-500/10 border-amber-500/20",
    emerald: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
  }
  const cls = colorMap[color] || colorMap.cyan

  return (
    <motion.div whileHover={{ y: -2 }} className="bg-[#0b1021]/80 backdrop-blur border border-slate-800/80 rounded-2xl p-5 relative overflow-hidden group">
      <div className={`absolute top-0 right-0 w-24 h-24 bg-current opacity-5 blur-2xl rounded-full -translate-y-1/2 translate-x-1/2 ${cls.split(" ")[0]}`} />
      <div className={`w-10 h-10 rounded-xl flex items-center justify-center mb-4 ${cls}`}>
        {icon}
      </div>
      <div className="text-3xl font-mono font-bold text-slate-100 mb-1 tracking-tight">{value}</div>
      <div className="text-xs uppercase tracking-wider font-semibold text-slate-500">{label}</div>
    </motion.div>
  )
}
