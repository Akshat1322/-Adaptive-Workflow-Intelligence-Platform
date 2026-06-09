"use client"

import { useState, useEffect } from "react"
import { Search, Brain, Target, ShieldAlert, Loader2 } from "lucide-react"
import { useWorkspaceStore, type KnowledgeCard } from "@/store/workspaceStore"
import { apiFetch } from "@/lib/api"
import { KnowledgeCardSkeleton } from "@/components/Skeleton"

export function KnowledgeBaseView() {
  const [query, setQuery] = useState("")
  const [isSearching, setIsSearching] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const results = useWorkspaceStore((state) => state.knowledgeResults)
  const setKnowledgeResults = useWorkspaceStore((state) => state.setKnowledgeResults)

  useEffect(() => {
    const loadExperiments = async () => {
      try {
        const res = await apiFetch("/api/knowledge", undefined, { silent: true })
        const data = await res.json()
        setKnowledgeResults(data.cards || [])
      } catch {
        // silent on initial load
      } finally {
        setIsLoading(false)
      }
    }
    loadExperiments()
  }, [setKnowledgeResults])

  const handleSearch = async () => {
    setIsSearching(true)
    try {
      const res = await apiFetch("/api/knowledge/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query }),
      })
      const data = await res.json()
      setKnowledgeResults(data.results || [])
    } catch {
      // toast shown by apiFetch
    } finally {
      setIsSearching(false)
    }
  }

  return (
    <div className="flex flex-col h-full space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 mb-1">Knowledge Workspace</h1>
          <p className="text-slate-400">Search historical experiments and domain intelligence.</p>
        </div>
      </div>

      <div className="relative mb-4">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-cyan-400 w-5 h-5" />
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleSearch()
          }}
          placeholder="Ask the knowledge base... (e.g. 'What worked best for HR datasets?')"
          disabled={isSearching}
          className="w-full bg-slate-900/60 border border-slate-700 rounded-xl pl-12 pr-36 py-4 text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 shadow-lg disabled:opacity-60"
        />
        <button
          onClick={handleSearch}
          disabled={isSearching}
          className="absolute right-2 top-1/2 -translate-y-1/2 bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
        >
          {isSearching ? <Loader2 className="w-4 h-4 animate-spin" /> : null}
          Semantic Search
        </button>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto pb-6 pr-2">
        {isLoading &&
          Array.from({ length: 3 }).map((_, i) => <KnowledgeCardSkeleton key={i} />)}
        {isSearching &&
          Array.from({ length: 2 }).map((_, i) => <KnowledgeCardSkeleton key={`search-${i}`} />)}
        {!isLoading && !isSearching && results.length === 0 && (
          <div className="text-center text-slate-500 py-12">
            No experiments stored yet. Upload a dataset and run orchestration to build knowledge.
          </div>
        )}
        {!isSearching &&
          results.map((item: KnowledgeCard, i: number) => (
            <div
              key={item.id || i}
              className="bg-[#0b1021]/80 backdrop-blur border border-slate-800 rounded-2xl p-5 hover:border-cyan-500/50 transition-colors group"
            >
              <div className="flex justify-between items-start mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-slate-900 flex items-center justify-center text-emerald-400 border border-slate-800">
                    <Brain className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-200">{item.dataset}</h3>
                    <div className="text-xs text-slate-500 uppercase tracking-widest">{item.domain}</div>
                  </div>
                </div>
                <div className="bg-emerald-500/10 text-emerald-400 px-3 py-1 rounded text-xs font-mono font-bold border border-emerald-500/20">
                  Match: {item.queryMatch}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 mb-4">
                <div className="bg-slate-900/50 rounded-xl p-3 border border-slate-800">
                  <div className="text-xs text-slate-500 uppercase mb-1 flex items-center gap-2">
                    <Target className="w-3 h-3" /> Pipeline Workflow
                  </div>
                  <div className="text-sm font-mono text-cyan-400">{item.workflow}</div>
                </div>
                <div className="bg-slate-900/50 rounded-xl p-3 border border-slate-800">
                  <div className="text-xs text-slate-500 uppercase mb-1 flex items-center gap-2">
                    <ShieldAlert className="w-3 h-3" /> Performance
                  </div>
                  <div className="text-sm font-mono text-violet-400">{item.performance}</div>
                </div>
              </div>

              <div className="bg-slate-800/30 rounded-xl p-3 border border-slate-700/30">
                <div className="text-xs text-slate-500 uppercase mb-1">Key Insight</div>
                <p className="text-sm text-slate-300">{item.insight}</p>
              </div>
            </div>
          ))}
      </div>
    </div>
  )
}
