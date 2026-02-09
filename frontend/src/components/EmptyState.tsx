import { ReactNode } from 'react'

interface EmptyStateProps {
  /** 主文案 */
  message: string
  /** 次要说明（可选） */
  description?: string
  /** 主操作按钮文案 */
  actionLabel: string
  /** 主操作：跳转或重试 */
  onAction: () => void
  /** 次要操作按钮文案（可选） */
  secondaryLabel?: string
  onSecondary?: () => void
  /** 是否高亮次要按钮（默认 false，主按钮高亮） */
  highlightSecondary?: boolean
  /** 自定义图标（可选） */
  icon?: ReactNode
}

const DEFAULT_ICON = (
  <svg className="w-14 h-14 text-foreground/30 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
  </svg>
)

export default function EmptyState({
  message,
  description,
  actionLabel,
  onAction,
  secondaryLabel,
  onSecondary,
  highlightSecondary = false,
  icon = DEFAULT_ICON,
}: EmptyStateProps) {
  return (
    <div className="bg-card border border-border rounded-xl p-10 text-center max-w-md mx-auto">
      {icon}
      <p className="text-foreground/90 font-medium mb-1">{message}</p>
      {description && <p className="text-foreground/60 text-sm mb-6">{description}</p>}
      {!description && <div className="mb-6" />}
      <div className="flex flex-wrap justify-center gap-3">
        <button
          onClick={onAction}
          className={`px-5 py-2.5 rounded-lg transition-opacity text-sm font-medium ${
            highlightSecondary
              ? 'border border-border hover:bg-background transition-colors'
              : 'bg-foreground text-background hover:opacity-90'
          }`}
        >
          {actionLabel}
        </button>
        {secondaryLabel && onSecondary && (
          <button
            onClick={onSecondary}
            className={`px-5 py-2.5 rounded-lg transition-all text-sm font-medium relative overflow-hidden ${
              highlightSecondary
                ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-lg hover:opacity-90 hover:scale-105 animate-button-pulse'
                : 'border border-border hover:bg-background transition-colors'
            }`}
          >
            {highlightSecondary && (
              <>
                <span className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer" />
                <span className="absolute inset-0 bg-gradient-to-r from-purple-500 to-pink-500 opacity-0 hover:opacity-100 transition-opacity duration-300" />
              </>
            )}
            <span className="relative z-10 font-semibold">{secondaryLabel}</span>
          </button>
        )}
      </div>
    </div>
  )
}
