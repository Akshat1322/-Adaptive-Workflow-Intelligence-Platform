"use client"

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

import { useWorkspaceStore } from '@/store/workspaceStore'

export default function ExperimentLab() {
  const leaderboard = useWorkspaceStore(state => state.leaderboard)
  const isOrchestrating = useWorkspaceStore(state => state.isOrchestrating)

  const data = leaderboard.length > 0
    ? leaderboard.map((item, index) => ({
        name: item.name.length > 12 ? item.name.slice(0, 12) + "…" : item.name,
        score: item.score,
        model: item.name,
        label: `Model ${index + 1}`,
      }))
    : []

  return (
    <div className="flex flex-col h-full space-y-6">
      <div className="flex justify-between items-end">
        <div>
          <h1 className="text-2xl font-bold text-slate-100 mb-1">Experiment Lab</h1>
          <p className="text-slate-400">Visual comparison of pipeline performance across runs.</p>
        </div>
      </div>
      
      <div className="flex-1 border border-slate-800 rounded-2xl bg-[#0b1021]/50 p-6 flex flex-col">
        {isOrchestrating ? (
          <div className="flex-1 flex flex-col items-center justify-center text-cyan-400 min-h-[300px]">
            <div className="w-10 h-10 border-2 border-cyan-500/30 border-t-cyan-400 rounded-full animate-spin mb-4" />
            <p>Running model benchmarks...</p>
          </div>
        ) : data.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center text-slate-500 min-h-[300px]">
            <p>No experiment results yet.</p>
            <p className="text-sm mt-1">Upload a dataset and orchestrate a pipeline to see the leaderboard.</p>
          </div>
        ) : (
          <>
            <h3 className="text-lg font-medium text-slate-300 mb-6">Model Leaderboard</h3>
            <div className="flex-1 min-h-[300px]">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                  <XAxis dataKey="name" stroke="#64748b" />
                  <YAxis stroke="#64748b" domain={[0, "auto"]} />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#0f172a", borderColor: "#1e293b", borderRadius: "8px" }}
                    itemStyle={{ color: "#06b6d4" }}
                  />
                  <Legend wrapperStyle={{ color: "#94a3b8" }} />
                  <Bar dataKey="score" fill="#8b5cf6" radius={[4, 4, 0, 0]} name="Validation Score" />
                </BarChart>
              </ResponsiveContainer>
            </div>

            <div className="mt-8 grid grid-cols-2 lg:grid-cols-4 gap-4">
              {data.map((exp, i) => (
                <div key={`${exp.model}-${i}`} className="bg-slate-900/50 border border-slate-800 rounded-xl p-4 transition-all hover:border-violet-500/50">
                  <div className="text-sm font-mono text-slate-500 mb-1">{exp.label}</div>
                  <div className="text-lg font-bold text-slate-200 truncate">{exp.model}</div>
                  <div className="text-2xl font-mono font-bold text-cyan-400 mt-2">{exp.score.toFixed(4)}</div>
                </div>
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
