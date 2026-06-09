"use client"

import { useEffect, useState } from "react"
import { GitCompareArrows, Loader2, UploadCloud } from "lucide-react"
import { apiFetch } from "@/lib/api"

interface DatasetRecord {
  name: string
  rows: number
  cols: number
  task_type: string
  uploaded_at: string
}

interface DriftResult {
  status: string
  message?: string
  drift_score?: number
  drifted_features?: string[]
  report?: string
  numeric_columns?: string[]
}

export function DriftMonitor() {
  const [datasets, setDatasets] = useState<DatasetRecord[]>([])
  const [active, setActive] = useState<string | null>(null)
  const [result, setResult] = useState<DriftResult | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isComparing, setIsComparing] = useState(false)

  useEffect(() => {
    const loadDatasets = async () => {
      try {
        const res = await apiFetch("/api/datasets", undefined, { silent: true })
        const data = await res.json()
        setDatasets(data.datasets || [])
        setActive(data.active || null)
      } catch {
        // keep empty state if backend has not started
      } finally {
        setIsLoading(false)
      }
    }
    loadDatasets()
  }, [])

  const handleCompare = async () => {
    setIsComparing(true)
    try {
      const res = await apiFetch("/api/drift/compare")
      const data = await res.json()
      setResult(data)
    } catch {
      // toast shown by apiFetch
    } finally {
      setIsComparing(false)
    }
  }

  const score = result?.drift_score ?? 0
  const severity =
    score > 0.35 ? "High" :
    score > 0.2 ? "Moderate" :
    result?.status === "success" ? "Stable" : "Waiting"

  return (
    <div className="flex flex-col h-full space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 mb-1">Drift Monitor</h1>
          <p className="text-slate-400">Compare the active dataset with the previous upload.</p>
        </div>
        <button
          onClick={handleCompare}
          disabled={isComparing || datasets.length < 2}
          className="bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white px-5 py-2.5 rounded-xl text-sm font-semibold transition-all flex items-center gap-2"
        >
          {isComparing ? <Loader2 className="w-4 h-4 animate-spin" /> : <GitCompareArrows className="w-4 h-4" />}
          Compare Drift
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div className="lg:col-span-1 border border-slate-800 rounded-2xl bg-[#0b1021]/50 p-5">
          <h2 className="text-sm font-bold uppercase tracking-wider text-slate-400 mb-4">Dataset History</h2>
          {isLoading ? (
            <div className="text-cyan-400 flex items-center gap-2 text-sm">
              <Loader2 className="w-4 h-4 animate-spin" /> Loading datasets
            </div>
          ) : datasets.length === 0 ? (
            <div className="text-slate-500 text-sm flex items-center gap-2">
              <UploadCloud className="w-4 h-4" /> Upload datasets to begin.
            </div>
          ) : (
            <div className="space-y-3">
              {datasets.slice(-5).reverse().map((dataset) => (
                <div
                  key={`${dataset.name}-${dataset.uploaded_at}`}
                  className={`rounded-xl border p-3 ${
                    dataset.name === active
                      ? "border-cyan-500/40 bg-cyan-500/10"
                      : "border-slate-800 bg-slate-900/40"
                  }`}
                >
                  <div className="font-semibold text-slate-200 truncate">{dataset.name}</div>
                  <div className="text-xs text-slate-500 mt-1">
                    {dataset.rows.toLocaleString()} rows · {dataset.cols} cols · {dataset.task_type}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="lg:col-span-2 border border-slate-800 rounded-2xl bg-[#0b1021]/50 p-6">
          {!result ? (
            <div className="h-full min-h-[260px] flex flex-col items-center justify-center text-slate-500">
              <GitCompareArrows className="w-10 h-10 mb-4 opacity-60" />
              <p>{datasets.length < 2 ? "Upload two datasets to enable drift comparison." : "Run a drift comparison to see stability signals."}</p>
            </div>
          ) : result.status === "insufficient_data" ? (
            <div className="text-slate-500 min-h-[260px] flex items-center justify-center">{result.message}</div>
          ) : (
            <div>
              <div className="grid grid-cols-3 gap-4 mb-6">
                <Metric label="Drift Score" value={score.toFixed(4)} />
                <Metric label="Severity" value={severity} />
                <Metric label="Numeric Checks" value={String(result.numeric_columns?.length ?? 0)} />
              </div>
              <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4 mb-4">
                <div className="text-xs text-slate-500 uppercase tracking-wider mb-2">Drifted Features</div>
                <div className="flex flex-wrap gap-2">
                  {(result.drifted_features?.length ? result.drifted_features : ["None"]).map((feature) => (
                    <span key={feature} className="px-2 py-1 rounded-lg bg-slate-800 text-slate-300 text-xs">
                      {feature}
                    </span>
                  ))}
                </div>
              </div>
              {result.report && (
                <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4 text-sm text-slate-300 whitespace-pre-wrap">
                  {result.report.replace(/\*\*/g, "")}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-4">
      <div className="text-xs text-slate-500 uppercase tracking-wider mb-1">{label}</div>
      <div className="text-2xl font-mono font-bold text-cyan-400">{value}</div>
    </div>
  )
}
