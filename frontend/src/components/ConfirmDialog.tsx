import { useEffect, useRef } from 'react'
import { X } from 'lucide-react'

interface ConfirmDialogProps {
  isOpen: boolean
  title: string
  message: string
  confirmText?: string
  cancelText?: string
  onConfirm: () => void
  onCancel: () => void
  showCancel?: boolean  // 是否显示取消按钮
}

export default function ConfirmDialog({
  isOpen,
  title,
  message,
  confirmText = '确认',
  cancelText = '取消',
  onConfirm,
  onCancel,
  showCancel = true,
}: ConfirmDialogProps) {
  const confirmButtonRef = useRef<HTMLButtonElement>(null)
  useEffect(() => {
    if (!isOpen) return
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onCancel()
    }
    window.addEventListener('keydown', onKeyDown)
    const t = setTimeout(() => confirmButtonRef.current?.focus(), 100)
    return () => {
      window.removeEventListener('keydown', onKeyDown)
      clearTimeout(t)
    }
  }, [isOpen, onCancel])
  if (!isOpen) return null

  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    // 如果点击的是背景蒙层（不是内容区域），则关闭
    if (e.target === e.currentTarget) {
      onCancel()
    }
  }

  return (
    <div 
      className="fixed inset-0 z-[10000] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
      onClick={handleBackdropClick}
    >
      <div 
        className="bg-card border border-border rounded-xl max-w-md w-full shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-foreground">{title}</h3>
            <button
              onClick={onCancel}
              className="p-1 rounded-full hover:bg-background transition-colors"
            >
              <X className="w-5 h-5 text-foreground/60" />
            </button>
          </div>
          <p className="text-foreground/80 mb-6">{message}</p>
          <div className="flex items-center justify-end space-x-3">
            {showCancel && (
              <button
                onClick={onCancel}
                className="px-4 py-2 text-sm border border-border rounded-lg hover:bg-background transition-colors"
              >
                {cancelText}
              </button>
            )}
            <button
              ref={confirmButtonRef}
              onClick={onConfirm}
              className="px-4 py-2 text-sm bg-purple-500 text-white rounded-lg hover:opacity-90 transition-opacity"
            >
              {confirmText}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
