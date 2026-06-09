"use client"

export function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div
      className={`animate-pulse rounded-lg bg-slate-800/80 ${className}`}
    />
  )
}

export function MetricCardSkeleton() {
  return (
    <div className="bg-[#0b1021]/80 border border-slate-800/80 rounded-2xl p-5">
      <Skeleton className="w-10 h-10 rounded-xl mb-4" />
      <Skeleton className="h-8 w-24 mb-2" />
      <Skeleton className="h-3 w-16" />
    </div>
  )
}

export function DatasetIntelligenceSkeleton() {
  return (
    <div className="animate-in fade-in duration-300">
      <div className="flex items-center justify-between mb-8">
        <div className="space-y-2">
          <Skeleton className="h-8 w-56" />
          <Skeleton className="h-4 w-40" />
        </div>
        <Skeleton className="h-8 w-36 rounded-full" />
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <MetricCardSkeleton key={i} />
        ))}
      </div>
      <div className="mt-8 bg-slate-900/60 border border-slate-800 rounded-2xl p-6">
        <div className="flex items-center justify-between mb-4">
          <Skeleton className="h-6 w-40" />
          <Skeleton className="h-10 w-44 rounded-xl" />
        </div>
        <Skeleton className="h-4 w-full mb-2" />
        <Skeleton className="h-4 w-3/4" />
      </div>
    </div>
  )
}

export function KnowledgeCardSkeleton() {
  return (
    <div className="bg-[#0b1021]/80 border border-slate-800 rounded-2xl p-5">
      <div className="flex justify-between items-start mb-4">
        <div className="flex items-center gap-3">
          <Skeleton className="w-10 h-10 rounded-full" />
          <div className="space-y-2">
            <Skeleton className="h-5 w-36" />
            <Skeleton className="h-3 w-24" />
          </div>
        </div>
        <Skeleton className="h-6 w-20 rounded" />
      </div>
      <div className="grid grid-cols-2 gap-4 mb-4">
        <Skeleton className="h-16 rounded-xl" />
        <Skeleton className="h-16 rounded-xl" />
      </div>
      <Skeleton className="h-20 rounded-xl" />
    </div>
  )
}

export function ReportSkeleton() {
  return (
    <div className="space-y-4">
      <Skeleton className="h-8 w-2/3" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-5/6" />
      <Skeleton className="h-6 w-1/2 mt-6" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-4/5" />
      <Skeleton className="h-6 w-1/3 mt-6" />
      <Skeleton className="h-4 w-full" />
      <Skeleton className="h-4 w-3/4" />
    </div>
  )
}
