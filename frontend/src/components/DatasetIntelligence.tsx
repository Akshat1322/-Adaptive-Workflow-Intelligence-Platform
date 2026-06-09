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
      <div className="flex-1 border-2 border-dashed border-white/10 hover:border-red-500/30 transition-colors rounded-3xl flex items-center justify-center bg-[#111111] min-h-[400px] shadow-lg group relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-b from-red-500/[0.02] to-transparent pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
        <div className="text-center relative z-10">
          <input
            type="file"
            accept=".csv"
            className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            onChange={handleFileUpload}
          />
          <div className="w-24 h-24 rounded-full bg-[#0A0A0A] border border-white/5 flex items-center justify-center mx-auto mb-8 shadow-[0_0_30px_rgba(225,29,72,0.1)] group-hover:shadow-[0_0_40px_rgba(225,29,72,0.2)] transition-shadow duration-500">
            <UploadCloud className="w-10 h-10 text-red-500" />
          </div>
          <h3 className="text-2xl font-bold text-neutral-100 mb-3 tracking-tight">Initialize Workspace</h3>
          <p className="text-neutral-500 text-sm max-w-md mx-auto leading-relaxed">
            Upload a CSV dataset to activate the AI Data Science Team. The Context Engine will immediately extract structural intelligence.
          </p>
          <div className="mt-8 inline-flex items-center gap-2 bg-white/[0.04] hover:bg-white/[0.08] text-neutral-300 px-6 py-3 rounded-full text-sm font-semibold transition-colors border border-white/5">
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
          <h2 className="text-2xl font-bold text-neutral-100 flex items-center gap-3 tracking-tight">
            <Fingerprint className="text-red-500 w-6 h-6" />
            Dataset Intelligence
          </h2>
          <p className="text-neutral-500 text-sm mt-1 font-mono">{String(intelligence.dataset ?? "")}</p>
        </div>
        <div className="bg-red-500/10 border border-red-500/20 text-red-400 px-4 py-1.5 rounded-full text-xs font-bold uppercase tracking-wider flex items-center gap-2 shadow-[0_0_15px_rgba(239,68,68,0.1)]">
          <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
          Extraction Complete
        </div>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard icon={<LayoutList />} label="Rows" value={Number(intelligence.rows ?? 0).toLocaleString()} color="red" />
        <MetricCard icon={<Database />} label="Columns" value={String(intelligence.cols ?? "0")} color="neutral" />
        <MetricCard icon={<Target />} label="Task Inference" value={String(intelligence.task_type ?? "unknown").replace("_", " ").toUpperCase()} color="red" />
        <MetricCard icon={<ShieldAlert />} label="Quality Score" value={`${Math.round(Number(intelligence.quality_score ?? 100))}%`} color={Number(intelligence.quality_score ?? 100) > 80 ? "neutral" : "red"} />
      </div>

      <div className="mt-8 bg-[#0A0A0A] border border-white/5 rounded-2xl p-8 shadow-lg relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-red-500/5 rounded-full blur-3xl -mt-32 -mr-32 pointer-events-none" />
        <div className="flex items-center justify-between mb-6 relative z-10">
          <h3 className="text-lg font-semibold text-neutral-100">Recommended Action</h3>
          <button
            onClick={handleOrchestrate}
            disabled={isOrchestrating}
            className="bg-red-600 hover:bg-red-500 disabled:opacity-50 disabled:hover:bg-red-600 text-white px-8 py-3 rounded-xl text-sm font-semibold shadow-[0_0_20px_rgba(220,38,38,0.2)] transition-all active:scale-95 flex items-center gap-3"
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
        <p className="text-neutral-400 text-sm leading-relaxed max-w-3xl relative z-10">
          The Data Agent suggests executing the default workflow pipeline. Watch the AI Copilot panel for live agent reasoning.
        </p>
      </div>
    </div>
  )
}

function MetricCard({ icon, label, value, color }: { icon: React.ReactNode; label: string; value: string; color: string }) {
  const colorMap: Record<string, string> = {
    red: "text-red-500 bg-red-500/10 border-red-500/20 shadow-[0_0_15px_rgba(239,68,68,0.05)]",
    neutral: "text-neutral-300 bg-white/5 border-white/10 shadow-sm",
  }
  const cls = colorMap[color] || colorMap.neutral

  return (
    <motion.div whileHover={{ y: -2 }} className="bg-[#111111] border border-white/5 rounded-2xl p-6 relative overflow-hidden group shadow-md">
      <div className={`absolute top-0 right-0 w-24 h-24 bg-current opacity-[0.03] blur-2xl rounded-full -translate-y-1/2 translate-x-1/2 ${cls.split(" ")[0]}`} />
      <div className={`w-12 h-12 rounded-xl flex items-center justify-center mb-5 ${cls}`}>
        {icon}
      </div>
      <div className="text-3xl font-mono font-bold text-neutral-100 mb-1.5 tracking-tight">{value}</div>
      <div className="text-[11px] uppercase tracking-widest font-semibold text-neutral-500">{label}</div>
    </motion.div>
  )
}
