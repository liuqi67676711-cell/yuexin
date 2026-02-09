import { useEffect } from 'react'
import { CheckCircle2, XCircle, Info, X } from 'lucide-react'

export type ToastType = 'success' | 'error' | 'info'

export interface Toast {
  id: string
  message: string
  type: ToastType
}

interface ToastProps {
  toast: Toast
  onClose: (id: string) => void
}

export default function Toast({ toast, onClose }: ToastProps) {
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose(toast.id)
    }, 3000)

    return () => clearTimeout(timer)
  }, [toast.id, onClose])

  const icons = {
    success: <CheckCircle2 className="w-5 h-5 text-green-600 dark:text-green-400 flex-shrink-0" />,
    error: <XCircle className="w-5 h-5 text-red-600 dark:text-red-400 flex-shrink-0" />,
    info: <Info className="w-5 h-5 text-blue-600 dark:text-blue-400 flex-shrink-0" />,
  }

  const bgColors = {
    success: 'bg-green-50 dark:bg-green-900/30 border-green-200 dark:border-green-700/50',
    error: 'bg-red-50 dark:bg-red-900/30 border-red-200 dark:border-red-700/50',
    info: 'bg-blue-50 dark:bg-blue-900/30 border-blue-200 dark:border-blue-700/50',
  }

  return (
    <div
      className={`flex items-center space-x-3 px-4 py-3 rounded-lg border shadow-lg backdrop-blur-sm ${bgColors[toast.type]} animate-fade-in`}
    >
      {icons[toast.type]}
      <p className="flex-1 text-sm text-foreground">{toast.message}</p>
      <button
        onClick={() => onClose(toast.id)}
        className="p-1 rounded hover:bg-black/10 dark:hover:bg-white/10 transition-colors"
      >
        <X className="w-4 h-4 text-foreground/60" />
      </button>
    </div>
  )
}
