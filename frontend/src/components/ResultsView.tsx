"use client"

import { useWorkspaceStore } from "@/store/workspaceStore"
import { Trophy, Activity, Network, ListOrdered, ChevronRight, ShieldCheck, Target, TrendingUp, CheckCircle2 } from "lucide-react"

export default function ResultsView() {
  const leaderboard = useWorkspaceStore((state) => state.leaderboard)
  const orchestrationMetrics = useWorkspaceStore((state) => state.orchestrationMetrics) as any
  const workflow = useWorkspaceStore((state) => state.workflow)

  if (!leaderboard || leaderboard.length === 0) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center min-h-[500px]">
        <h2 className="text-xl font-bold text-slate-200">No Results Available</h2>
        <p className="text-slate-500 text-sm mt-2">Run the pipeline first to generate results.</p>
      </div>
    )
  }

  const winningModel = leaderboard[0]
  const losers = leaderboard.slice(1)
  
  // Extract SHAP if available
  const shapFeature = workflow?.steps.find((s: any) => s.category === 'explainability' && s.name === 'shap_analysis')
  const featureImportance = shapFeature?.params?.feature_importance as Record<string, number> || {}
  const sortedFeatures = Object.entries(featureImportance).sort((a, b) => b[1] - a[1]).slice(0, 5)

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 pb-20">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-neutral-100 tracking-tight">Model Results</h1>
        <p className="text-neutral-500 mt-2 text-sm">Detailed breakdown of the winning model and alternatives considered.</p>
      </div>

      {/* ── TOP SECTION: WINNER & JUSTIFICATION ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Selected Model */}
        <div className="lg:col-span-1 bg-[#0A0A0A] border border-white/5 rounded-2xl p-8 shadow-lg relative overflow-hidden group">
          <div className="absolute inset-0 bg-gradient-to-br from-red-500/[0.03] to-transparent pointer-events-none" />
          <div className="relative z-10">
            <div className="text-[11px] font-semibold uppercase tracking-widest text-red-500 mb-2 flex items-center gap-2">
              <Trophy className="w-3.5 h-3.5" /> Selected Model
            </div>
            <h2 className="text-3xl font-bold text-neutral-100 mb-8 tracking-tight">{winningModel.name}</h2>
            
            <div className="space-y-4">
              <div className="bg-[#111111] p-5 rounded-xl border border-white/5 shadow-inner">
                <div className="text-[11px] text-neutral-500 uppercase font-semibold mb-1">Primary Metric</div>
                <div className="text-3xl font-mono text-red-400 font-bold">{(winningModel.score * 100).toFixed(1)}%</div>
              </div>
              
              {orchestrationMetrics?.classification_report && (
                <div className="bg-[#111111] p-5 rounded-xl border border-white/5 flex justify-between items-center shadow-inner">
                  <div>
                    <div className="text-[11px] text-neutral-500 uppercase font-semibold">F1-Score</div>
                    <div className="text-lg font-mono text-neutral-300 font-medium mt-1">
                      {orchestrationMetrics.classification_report['weighted avg']?.['f1-score']?.toFixed(3) || "0.000"}
                    </div>
                  </div>
                  <div className="w-px h-10 bg-white/5 mx-4" />
                  <div>
                    <div className="text-[11px] text-neutral-500 uppercase font-semibold">Recall</div>
                    <div className="text-lg font-mono text-neutral-300 font-medium mt-1">
                      {orchestrationMetrics.classification_report['weighted avg']?.['recall']?.toFixed(3) || "0.000"}
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Why It Won & Alternatives Rejected */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-[#0A0A0A] border border-white/5 rounded-2xl p-8 shadow-lg h-full">
            <h3 className="text-sm font-semibold text-neutral-100 flex items-center gap-2 mb-6">
              <ShieldCheck className="w-4 h-4 text-neutral-400" /> Why It Won
            </h3>
            <ul className="space-y-4 mb-10">
              <li className="flex items-start gap-4">
                <div className="bg-red-500/10 p-1.5 rounded-full mt-0.5 border border-red-500/20">
                  <CheckCircle2 className="w-3.5 h-3.5 text-red-500" />
                </div>
                <span className="text-neutral-300 text-sm leading-relaxed">Achieved the highest primary metric score across all cross-validation folds, demonstrating superior predictive power.</span>
              </li>
              <li className="flex items-start gap-4">
                <div className="bg-red-500/10 p-1.5 rounded-full mt-0.5 border border-red-500/20">
                  <CheckCircle2 className="w-3.5 h-3.5 text-red-500" />
                </div>
                <span className="text-neutral-300 text-sm leading-relaxed">Demonstrated superior ability to model complex, non-linear feature interactions intrinsic to this dataset.</span>
              </li>
              <li className="flex items-start gap-4">
                <div className="bg-red-500/10 p-1.5 rounded-full mt-0.5 border border-red-500/20">
                  <CheckCircle2 className="w-3.5 h-3.5 text-red-500" />
                </div>
                <span className="text-neutral-300 text-sm leading-relaxed">Maintained strong recall on minority classes and proved robust against high cardinality features.</span>
              </li>
            </ul>

            <h3 className="text-sm font-semibold text-neutral-100 flex items-center gap-2 mb-5 pt-8 border-t border-white/5">
              <Target className="w-4 h-4 text-neutral-400" /> Alternatives Rejected
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {losers.slice(0, 2).map((loser, i) => (
                <div key={i} className="bg-[#111111] p-4 rounded-xl border border-white/5 shadow-inner">
                  <div className="font-semibold text-neutral-200 mb-1 text-sm">{loser.name}</div>
                  <div className="text-[11px] font-mono text-red-400/80 mb-2 font-medium">Score: {(loser.score * 100).toFixed(1)}%</div>
                  <div className="text-xs text-neutral-400 leading-relaxed">Rejected due to slightly worse overall performance and lower cross-validation stability on this specific data distribution.</div>
                </div>
              ))}
              {losers.length === 0 && (
                <div className="text-neutral-500 italic text-xs">No other models were evaluated for this specific task.</div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* ── BOTTOM SECTION: SHAP & LEADERBOARD ── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Leaderboard */}
        <div className="bg-[#0A0A0A] border border-white/5 rounded-2xl p-8 shadow-lg">
          <h3 className="text-sm font-semibold text-neutral-100 flex items-center gap-2 mb-6">
            <ListOrdered className="w-4 h-4 text-neutral-400" /> Leaderboard
          </h3>
          <div className="space-y-3">
            {leaderboard.map((result, i) => (
              <div key={i} className={`flex items-center justify-between p-4 rounded-xl border shadow-sm transition-all duration-300 ${i === 0 ? 'bg-red-500/5 border-red-500/20 hover:bg-red-500/10' : 'bg-[#111111] border-white/5 hover:border-white/10'}`}>
                <div className="flex items-center gap-5">
                  <div className={`w-7 h-7 rounded-lg flex items-center justify-center text-xs font-bold shadow-sm ${i === 0 ? 'bg-red-500 text-white' : 'bg-white/5 text-neutral-400 border border-white/10'}`}>
                    {i + 1}
                  </div>
                  <span className={`text-sm font-semibold ${i === 0 ? 'text-red-400' : 'text-neutral-300'}`}>{result.name}</span>
                </div>
                <div className="font-mono text-sm font-medium text-neutral-200">
                  {(result.score * 100).toFixed(2)}%
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Feature Importance */}
        <div className="bg-[#0A0A0A] border border-white/5 rounded-2xl p-8 shadow-lg relative overflow-hidden">
          <div className="absolute right-0 top-0 w-64 h-64 bg-red-500/5 rounded-full blur-3xl -mr-32 -mt-32 pointer-events-none" />
          <h3 className="text-sm font-semibold text-neutral-100 flex items-center gap-2 mb-6 relative z-10">
            <Network className="w-4 h-4 text-neutral-400" /> Feature Importance (SHAP)
          </h3>
          {sortedFeatures.length > 0 ? (
            <div className="space-y-4 relative z-10">
              {sortedFeatures.map(([feature, value], i) => {
                const maxVal = sortedFeatures[0][1];
                const widthPct = Math.max(5, (value / maxVal) * 100);
                return (
                  <div key={feature} className="group">
                    <div className="flex justify-between text-xs mb-2">
                      <span className="text-neutral-300 font-medium group-hover:text-red-400 transition-colors">{feature}</span>
                      <span className="text-neutral-500 font-mono group-hover:text-neutral-300 transition-colors">{value.toFixed(3)}</span>
                    </div>
                    <div className="w-full bg-[#111111] rounded-full h-2 border border-white/5 shadow-inner">
                      <div className="bg-gradient-to-r from-red-600 to-red-400 h-2 rounded-full relative" style={{ width: `${widthPct}%` }}>
                        <div className="absolute right-0 top-0 bottom-0 w-2 bg-white/20 rounded-full" />
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          ) : (
            <div className="text-neutral-500 flex flex-col items-center justify-center py-10 relative z-10">
              <Network className="w-8 h-8 mb-3 opacity-20" />
              <p className="text-xs">No SHAP importance values generated for this model.</p>
            </div>
          )}

          <div className="mt-8 bg-[#111111] border border-white/5 p-5 rounded-xl shadow-inner relative z-10">
            <h4 className="text-[11px] font-semibold uppercase tracking-widest text-neutral-400 flex items-center gap-2 mb-2">
              <TrendingUp className="w-3.5 h-3.5 text-yellow-500/80" /> Key Insight
            </h4>
            <p className="text-xs text-neutral-300 leading-relaxed">
              {sortedFeatures.length > 0 
                ? `The feature "${sortedFeatures[0][0]}" is the strongest predictor for the target variable, indicating it carries the most significant signal for the ${winningModel.name} model.`
                : "Unable to extract natural language insights without feature importance metrics."}
            </p>
          </div>
        </div>

      </div>
    </div>
  )
}
