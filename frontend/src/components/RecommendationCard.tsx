import { useState } from 'react'
import { BookOpen, Star, X } from 'lucide-react'
import { RecommendationItem } from '../api/recommendation'
import BookCoverPlaceholder from './BookCoverPlaceholder'
import { bookshelfAPI } from '../api/bookshelf'
import { showToast } from './ToastContainer'
import ConfirmDialog from './ConfirmDialog'

interface RecommendationCardProps {
  item: RecommendationItem
  onRemove: (bookId: number) => void
  onViewDetails: (bookId: number) => void
  onAskAgent: (bookId: number, bookTitle?: string) => void
}

export default function RecommendationCard({
  item,
  onRemove,
  onViewDetails,
  onAskAgent,
}: RecommendationCardProps) {
  const [showConfirm, setShowConfirm] = useState(false)

  const handleNotInterested = async () => {
    setShowConfirm(true)
  }

  const confirmNotInterested = async () => {
    setShowConfirm(false)
    try {
      await bookshelfAPI.markNotInterested(item.book_id)
      onRemove(item.book_id)
      showToast('已标记为不感兴趣', 'success')
    } catch (error: any) {
      console.error('标记不感兴趣失败:', error)
      showToast('操作失败，请稍后重试', 'error')
    }
  }

  // 高亮推荐语中的一句话（随机选择）
  const highlightText = (text: string, words: string[]) => {
    if (!words || words.length === 0) return text

    let highlightedText = text
    // 如果 words 数组中有完整的句子，高亮该句子
    // 否则高亮第一个匹配的词
    const sentenceToHighlight = words.find(word => word.length > 10) || words[0]
    
    if (sentenceToHighlight) {
      // 转义特殊字符用于正则表达式
      const escaped = sentenceToHighlight.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
      const regex = new RegExp(`(${escaped})`, 'gi')
      highlightedText = highlightedText.replace(
        regex,
        '<mark class="bg-purple-500/25 text-purple-600 dark:text-purple-300 px-1 rounded font-medium">$1</mark>'
      )
    }
    return highlightedText
  }

  return (
    <div className="relative glass-card border border-border/50 rounded-2xl p-8 hover:shadow-2xl transition-all duration-300 hover:scale-[1.02] backdrop-blur-xl">
      {/* 不感兴趣按钮 */}
      <button
        onClick={handleNotInterested}
        className="absolute top-4 right-4 p-1 rounded-full hover:bg-background transition-colors"
        title="不感兴趣"
      >
        <X className="w-4 h-4 text-foreground/60" />
      </button>

      <div className="flex flex-col gap-6">
        <div className="flex flex-col md:flex-row gap-6">
          {/* 左侧：推荐语 + 操作按钮（平分卡片宽度） */}
          <div className="flex-1 flex flex-col gap-4">
            <p
              className="text-xl md:text-2xl leading-relaxed text-foreground font-light"
              style={{ lineHeight: '1.8' }}
              dangerouslySetInnerHTML={{
                __html: highlightText(item.recommendation_text, item.highlighted_words),
              }}
            />
            <div className="flex gap-3 w-full">
              <button
                onClick={() => onViewDetails(item.book_id)}
                className="flex-1 px-5 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-xl hover:opacity-90 transition-all text-sm font-medium"
              >
                去看看
              </button>
              <button
                onClick={() => onAskAgent(item.book_id, item.title)}
                className="flex-1 px-5 py-3 border border-border/50 rounded-xl hover:bg-background/50 transition-all text-sm flex items-center justify-center gap-1.5 backdrop-blur-sm"
              >
                <BookOpen className="w-4 h-4 flex-shrink-0" />
                <span>这本书讲什么了</span>
              </button>
            </div>
          </div>

          {/* 右侧：书籍信息 */}
          <div className="flex-shrink-0 w-full md:w-48 flex flex-col">
            <div className="w-full h-56 rounded-lg mb-3 overflow-hidden">
              {item.cover_url ? (
                <img
                  src={item.cover_url}
                  alt={item.title}
                  className="w-full h-full object-cover"
                  loading="lazy"
                  decoding="async"
                />
              ) : (
                <BookCoverPlaceholder title={item.title} className="w-full h-full rounded-lg" />
              )}
            </div>
            <h3 className="font-semibold text-foreground text-lg mb-1 line-clamp-2">{item.title}</h3>
            <p className="text-sm text-foreground/70 mb-2">{item.author}</p>
            {item.rating > 0 && (
              <div className="flex items-center space-x-1">
                <Star className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                <span className="text-sm text-foreground/70">{item.rating.toFixed(1)}</span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 不感兴趣确认对话框 */}
      <ConfirmDialog
        isOpen={showConfirm}
        title="不感兴趣"
        message={`确定要将《${item.title}》标记为不感兴趣吗？这将帮助系统更好地为你推荐书籍。`}
        confirmText="确认"
        cancelText="取消"
        onConfirm={confirmNotInterested}
        onCancel={() => setShowConfirm(false)}
      />
    </div>
  )
}
