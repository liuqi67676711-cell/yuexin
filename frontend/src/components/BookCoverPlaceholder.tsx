/**
 * 书籍封面占位图：无封面时显示统一背景色 + 书名 + 暂无封面提示
 */
interface BookCoverPlaceholderProps {
  title: string
  className?: string
}

export default function BookCoverPlaceholder({ title, className = '' }: BookCoverPlaceholderProps) {
  const displayTitle = title.length > 12 ? title.slice(0, 12) + '...' : title
  return (
    <div
      className={`flex flex-col items-center justify-center bg-gradient-to-br from-indigo-500 to-purple-600 text-white text-center overflow-hidden ${className}`}
      title={title}
    >
      <span className="text-sm font-medium px-2 line-clamp-2 leading-tight" style={{ fontSize: 'clamp(10px, 2.5vw, 14px)' }}>
        {displayTitle}
      </span>
      <span className="text-[10px] opacity-80 mt-1">暂无封面</span>
    </div>
  )
}
