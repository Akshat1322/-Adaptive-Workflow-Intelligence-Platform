"use client"

import { useState } from "react"
import { FileText, Download, Loader2 } from "lucide-react"
import { useWorkspaceStore } from "@/store/workspaceStore"
import { apiFetch, showError } from "@/lib/api"
import { ReportSkeleton } from "@/components/Skeleton"

function MarkdownPreview({ content }: { content: string }) {
  const lines = content.split("\n")
  return (
    <div className="prose prose-invert max-w-none space-y-3 text-slate-300">
      {lines.map((line, i) => {
        if (line.startsWith("# ")) {
          return (
            <h1 key={i} className="text-2xl font-bold text-slate-100 mt-4">
              {line.slice(2)}
            </h1>
          )
        }
        if (line.startsWith("## ")) {
          return (
            <h2 key={i} className="text-xl font-semibold text-slate-200 mt-4">
              {line.slice(3)}
            </h2>
          )
        }
        if (line.startsWith("### ")) {
          return (
            <h3 key={i} className="text-lg font-semibold text-slate-200 mt-3">
              {line.slice(4)}
            </h3>
          )
        }
        if (line.startsWith("- ")) {
          const text = line.slice(2).replace(/\*\*(.*?)\*\*/g, "$1")
          return (
            <li key={i} className="ml-4 list-disc text-slate-300">
              {text}
            </li>
          )
        }
        if (!line.trim()) return <div key={i} className="h-2" />
        const html = line.replace(/\*\*(.*?)\*\*/g, '<strong class="text-slate-100">$1</strong>')
        return <p key={i} className="leading-relaxed" dangerouslySetInnerHTML={{ __html: html }} />
      })}
    </div>
  )
}

export function ReportStudio() {
  const reportMarkdown = useWorkspaceStore((state) => state.reportMarkdown)
  const setReportMarkdown = useWorkspaceStore((state) => state.setReportMarkdown)
  const orchestrationMetrics = useWorkspaceStore((state) => state.orchestrationMetrics)
  const [isGenerating, setIsGenerating] = useState(false)

  const handleGenerate = async () => {
    setIsGenerating(true)
    try {
      const res = await apiFetch("/api/report/generate", { method: "POST" })
      const data = await res.json()
      if (data.error) {
        showError(data.error)
      } else {
        setReportMarkdown(data.markdown)
      }
    } catch {
      // toast shown by apiFetch
    } finally {
      setIsGenerating(false)
    }
  }

  const handleDownload = () => {
    if (!reportMarkdown) return
    const blob = new Blob([reportMarkdown], { type: "text/markdown" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = "AWIP_Report.md"
    a.click()
    URL.revokeObjectURL(url)
  }

  const handleServerExport = (format: "pdf" | "docx") => {
    window.open(`/api/report/export/${format}`, "_blank")
  }

  const hasOrchestration = !!orchestrationMetrics || !!reportMarkdown

  return (
    <div className="flex flex-col h-full space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 mb-1">Report Studio</h1>
          <p className="text-slate-400">Generate, export, and share automated research findings.</p>
        </div>
        <button
          onClick={handleGenerate}
          disabled={isGenerating}
          className="bg-gradient-to-r from-violet-600 to-indigo-600 hover:from-violet-500 hover:to-indigo-500 disabled:opacity-50 text-white px-5 py-2.5 rounded-xl text-sm font-semibold transition-all shadow-lg shadow-indigo-900/20 flex items-center gap-2"
        >
          {isGenerating ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
          Generate New Report
        </button>
      </div>

      <div className="flex-1 border border-slate-800 rounded-2xl bg-[#0b1021]/50 p-6 flex flex-col">
        {isGenerating ? (
          <ReportSkeleton />
        ) : !hasOrchestration && !reportMarkdown ? (
          <div className="flex-1 flex flex-col justify-center items-center">
            <div className="w-20 h-20 rounded-full bg-slate-900 flex items-center justify-center text-slate-500 border border-slate-800 mb-6">
              <FileText className="w-10 h-10" />
            </div>
            <h3 className="text-xl font-bold text-slate-200 mb-2">No Reports Generated</h3>
            <p className="text-slate-500 text-center max-w-sm">
              Execute a workflow pipeline first to generate automated analysis and executive summaries.
            </p>
          </div>
        ) : reportMarkdown ? (
          <>
            <div className="flex justify-end gap-2 mb-4">
              <button
                onClick={handleDownload}
                className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm transition-colors border border-slate-700"
              >
                <Download className="w-4 h-4" /> Export Markdown
              </button>
              <button
                onClick={() => handleServerExport("pdf")}
                className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm transition-colors border border-slate-700"
              >
                <Download className="w-4 h-4" /> PDF
              </button>
              <button
                onClick={() => handleServerExport("docx")}
                className="flex items-center gap-2 px-4 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-sm transition-colors border border-slate-700"
              >
                <Download className="w-4 h-4" /> DOCX
              </button>
            </div>
            <div className="flex-1 overflow-y-auto pr-2">
              <MarkdownPreview content={reportMarkdown} />
            </div>
          </>
        ) : (
          <div className="flex-1 flex flex-col justify-center items-center text-slate-500">
            <p className="mb-4">Orchestration complete. Click &quot;Generate New Report&quot; to compile findings.</p>
          </div>
        )}
      </div>
    </div>
  )
}
