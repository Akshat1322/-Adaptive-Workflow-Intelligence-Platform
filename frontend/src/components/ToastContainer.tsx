"use client"

import { AnimatePresence, motion } from "framer-motion"
import { X, AlertCircle, CheckCircle2, Info } from "lucide-react"
import { useToastStore } from "@/store/toastStore"

const icons = {
  error: AlertCircle,
  success: CheckCircle2,
  info: Info,
}

const styles = {
  error: "border-red-500/30 bg-red-500/10 text-red-300",
  success: "border-emerald-500/30 bg-emerald-500/10 text-emerald-300",
  info: "border-cyan-500/30 bg-cyan-500/10 text-cyan-300",
}

export function ToastContainer() {
  const toasts = useToastStore((state) => state.toasts)
  const removeToast = useToastStore((state) => state.removeToast)

  return (
    <div className="fixed bottom-6 right-6 z-[100] flex flex-col gap-2 max-w-sm pointer-events-none">
      <AnimatePresence>
        {toasts.map((toast) => {
          const Icon = icons[toast.type]
          return (
            <motion.div
              key={toast.id}
              initial={{ opacity: 0, y: 20, scale: 0.95 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, x: 40, scale: 0.95 }}
              className={`pointer-events-auto flex items-start gap-3 px-4 py-3 rounded-xl border backdrop-blur-xl shadow-xl ${styles[toast.type]}`}
            >
              <Icon className="w-5 h-5 shrink-0 mt-0.5" />
              <p className="text-sm leading-relaxed flex-1">{toast.message}</p>
              <button
                onClick={() => removeToast(toast.id)}
                className="shrink-0 opacity-60 hover:opacity-100 transition-opacity"
              >
                <X className="w-4 h-4" />
              </button>
            </motion.div>
          )
        })}
      </AnimatePresence>
    </div>
  )
}
