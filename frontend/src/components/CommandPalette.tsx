"use client"

import { useEffect, useState } from 'react'
import { Search, BarChart2, Zap, Book } from 'lucide-react'
import { apiFetch, showSuccess } from '@/lib/api'
import { useWorkspaceStore } from '@/store/workspaceStore'
import { runWorkspaceOrchestration } from '@/lib/orchestration'

export function CommandPalette({ open, setOpen, onNavigate }: { open: boolean, setOpen: (v: boolean) => void, onNavigate: (page: string) => void }) {
  const [query, setQuery] = useState('')
  const [isProcessing, setIsProcessing] = useState(false)

  // Toggle the menu when ⌘K is pressed
  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault()
        setOpen(!open)
      }
    }
    document.addEventListener('keydown', down)
    return () => document.removeEventListener('keydown', down)
  }, [open, setOpen])

  const handleCommand = async (cmd: string) => {
    setIsProcessing(true)
    const { appendChatMessage } = useWorkspaceStore.getState()

    try {
      appendChatMessage({
        role: 'user',
        content: cmd,
        timestamp: new Date().toISOString(),
      })
      const res = await apiFetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command: cmd }),
      })
      const data = await res.json()
      appendChatMessage({
        role: 'assistant',
        content: data.response || 'Command received.',
        timestamp: new Date().toISOString(),
        intent: data.intent,
      })

      if (data.intent === "NAVIGATE" || data.intent === "GENERATE_REPORT") {
        if (cmd.toLowerCase().includes("report")) onNavigate("reports")
        else if (cmd.toLowerCase().includes("experiment")) onNavigate("experiments")
        else if (cmd.toLowerCase().includes("knowledge")) onNavigate("knowledge")
        else onNavigate("home")
      } else if (data.intent === "EXECUTE") {
        onNavigate("workflow")
        runWorkspaceOrchestration()
      } else {
        showSuccess('Copilot response added to the side panel')
      }
    } catch {
      // toast shown by apiFetch
    } finally {
      setIsProcessing(false)
      setOpen(false)
      setQuery('')
    }
  }

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-start justify-center pt-[15vh]">
      <div className="bg-[#0b1021] border border-slate-700 w-full max-w-2xl rounded-2xl shadow-2xl overflow-hidden flex flex-col animate-in fade-in zoom-in-95 duration-200">
        
        <div className="flex items-center px-4 border-b border-slate-800">
          <Search className="w-5 h-5 text-slate-500 shrink-0" />
          <input 
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && query) {
                handleCommand(query)
              } else if (e.key === 'Escape') {
                setOpen(false)
              }
            }}
            className="w-full bg-transparent border-none py-4 pl-3 pr-4 text-slate-200 placeholder:text-slate-500 focus:outline-none focus:ring-0 text-lg"
            placeholder="Type a command or ask the AI..."
          />
          {isProcessing && <div className="w-4 h-4 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin shrink-0" />}
          <div className="flex gap-1 ml-2 shrink-0">
            <kbd className="bg-slate-800 text-slate-400 px-2 py-1 rounded text-xs">ESC</kbd>
          </div>
        </div>

        {!query && (
          <div className="p-2 space-y-1">
            <div className="px-3 py-2 text-xs font-semibold text-slate-500 uppercase tracking-wider">Suggested Actions</div>
            <button onClick={() => { setQuery("Generate an executive report"); handleCommand("Generate an executive report") }} className="w-full flex items-center gap-3 px-3 py-3 text-sm text-slate-300 hover:bg-slate-800/50 hover:text-cyan-400 rounded-lg transition-colors text-left">
              <BarChart2 className="w-4 h-4" /> Generate an executive report
            </button>
            <button onClick={() => { setQuery("Compare latest experiments"); handleCommand("Compare latest experiments") }} className="w-full flex items-center gap-3 px-3 py-3 text-sm text-slate-300 hover:bg-slate-800/50 hover:text-violet-400 rounded-lg transition-colors text-left">
              <Zap className="w-4 h-4" /> Compare latest experiments
            </button>
            <button onClick={() => { setQuery("What worked best for HR datasets?"); handleCommand("What worked best for HR datasets?") }} className="w-full flex items-center gap-3 px-3 py-3 text-sm text-slate-300 hover:bg-slate-800/50 hover:text-emerald-400 rounded-lg transition-colors text-left">
              <Book className="w-4 h-4" /> Query Knowledge Base
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
