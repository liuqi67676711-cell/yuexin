import { X } from 'lucide-react'

interface ChoiceDialogProps {
  isOpen: boolean
  title: string
  message: string
  primaryText: string
  secondaryText: string
  onPrimary: () => void
  onSecondary: () => void
  onCancel: () => void
}

export default function ChoiceDialog({
  isOpen,
  title,
  message,
  primaryText,
  secondaryText,
  onPrimary,
  onSecondary,
  onCancel,
}: ChoiceDialogProps) {
  if (!isOpen) return null

  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    // 如果点击的是背景蒙层（不是内容区域），则关闭
    if (e.target === e.currentTarget) {
      onCancel()
    }
  }

  return (
    <div 
      className="fixed inset-0 z-[10001] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm"
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
            <button
              onClick={onCancel}
              className="px-4 py-2 text-sm border border-border rounded-lg hover:bg-background transition-colors"
            >
              取消
            </button>
            <button
              onClick={onSecondary}
              className="px-4 py-2 text-sm border border-border rounded-lg hover:bg-background transition-colors"
            >
              {secondaryText}
            </button>
            <button
              onClick={onPrimary}
              className="px-4 py-2 text-sm bg-purple-500 text-white rounded-lg hover:opacity-90 transition-opacity"
            >
              {primaryText}
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
