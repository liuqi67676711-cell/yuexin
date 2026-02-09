import { useState, useCallback, useEffect } from 'react'
import Toast, { Toast as ToastType } from './Toast'

let toastIdCounter = 0
let addToastFn: ((message: string, type: ToastType['type']) => void) | null = null

export function showToast(message: string, type: ToastType['type'] = 'info') {
  if (addToastFn) {
    addToastFn(message, type)
  }
}

export default function ToastContainer() {
  const [toasts, setToasts] = useState<ToastType[]>([])

  const addToast = useCallback((message: string, type: ToastType['type'] = 'info') => {
    const id = `toast-${++toastIdCounter}`
    setToasts((prev) => [...prev, { id, message, type }])
  }, [])

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id))
  }, [])

  // 设置全局函数
  useEffect(() => {
    addToastFn = addToast
    return () => {
      addToastFn = null
    }
  }, [addToast])

  if (toasts.length === 0) return null

  return (
    <div className="fixed top-20 right-4 z-[9999] space-y-2 max-w-md">
      {toasts.map((toast) => (
        <Toast key={toast.id} toast={toast} onClose={removeToast} />
      ))}
    </div>
  )
}
