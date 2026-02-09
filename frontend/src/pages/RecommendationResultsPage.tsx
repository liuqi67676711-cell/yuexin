import { useState, useEffect, useRef, useMemo } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import RecommendationCard from '../components/RecommendationCard'
import BookDetailModal from '../components/BookDetailModal'
import AgentChatModal from '../components/AgentChatModal'
import LoadingSpinner from '../components/LoadingSpinner'
import EmptyState from '../components/EmptyState'
import { RecommendationItem } from '../api/recommendation'
import { recommendationAPI } from '../api/recommendation'
import { booksAPI, Book } from '../api/books'
import { showToast } from '../components/ToastContainer'
import { ArrowLeft, RefreshCw } from 'lucide-react'

/** 换一批时随机展示的暖心/阅读相关短句，缓解等待焦虑 */
const REFRESH_CARE_TIPS = [
  '好书值得多等一会儿～',
  '正在为你挑书，马上就好',
  '阅读是送给自己的小憩',
  '稍等片刻，更多好书正在赶来',
  '每一本都是为你认真选的',
  '好的下一本，值得这点等待',
  '正在书海里帮你捞宝贝',
  '别急，好故事正在排队见你',
]

export default function RecommendationResultsPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const query = searchParams.get('q') || ''
  
  const [recommendations, setRecommendations] = useState<RecommendationItem[]>([])
  const [message, setMessage] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [showAgentSuggestion, setShowAgentSuggestion] = useState(false)
  const [_agentName, setAgentName] = useState('苏童童')
  const [selectedBook, setSelectedBook] = useState<Book | null>(null)
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false)
  const [isAgentModalOpen, setIsAgentModalOpen] = useState(false)
  const [selectedBookId, setSelectedBookId] = useState<number | null>(null)
  const [selectedBookTitleForAsk, setSelectedBookTitleForAsk] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)
  /** 当前请求 id：只应用「当前请求」的响应，避免竞态下先收到空结果把页面刷成「未找到」再被后续结果覆盖 */
  const requestIdRef = useRef(0)
  /** 本次加载是否曾有过推荐结果（用于区分「API 返回空」与「用户全部标记不感兴趣」） */
  const hadRecommendationsRef = useRef(false)
  /** 换一批时展示的随机暖心短句（每次进入加载态随机选一条） */
  const refreshCareTip = useMemo(
    () => REFRESH_CARE_TIPS[Math.floor(Math.random() * REFRESH_CARE_TIPS.length)],
    [isLoading]
  )

  useEffect(() => {
    document.title = query ? `阅心 - 为你推荐：${query}` : '阅心 - 为你推荐'
    return () => { document.title = '阅心' }
  }, [query])
  useEffect(() => {
    if (query) {
      // 检查缓存：如果查询参数相同，直接使用缓存的结果
      const cacheKey = `recommendation_results_${query}`
      const cachedData = sessionStorage.getItem(cacheKey)
      if (cachedData) {
        try {
          const cached = JSON.parse(cachedData)
          // 检查缓存是否过期（5分钟内有效）
          if (Date.now() - cached.timestamp < 5 * 60 * 1000) {
            hadRecommendationsRef.current = (cached.recommendations?.length ?? 0) > 0
            setRecommendations(cached.recommendations)
            setMessage(cached.message)
            setShowAgentSuggestion(cached.show_agent_suggestion || false)
            setAgentName(cached.agent_name || '苏童童')
            setIsLoading(false)
            return
          }
        } catch (e) {
          // 缓存解析失败，继续正常加载
        }
      }
      loadRecommendations(query)
    } else {
      setIsLoading(false)
    }
    return () => {
      if (abortRef.current) abortRef.current.abort()
    }
  }, [query])

  /** 换一批时保留当前列表，仅叠加加载态，新结果返回后再替换；支持请求取消；忽略过时响应避免先显示「未找到」再出结果 */
  const loadRecommendations = async (searchQuery: string, _keepCurrentList = false) => {
    if (abortRef.current) abortRef.current.abort()
    abortRef.current = new AbortController()
    const signal = abortRef.current.signal
    const thisRequestId = ++requestIdRef.current
    const hadList = recommendations.length > 0
    const loadingStartedAt = Date.now()
    const MIN_LOADING_MS = 600 // 换一批时至少展示 600ms 加载动效，避免请求过快时看不到
    setIsLoading(true)
    try {
      const response = await recommendationAPI.semanticRecommendation(searchQuery, signal)
      if (thisRequestId !== requestIdRef.current) return
      const elapsed = Date.now() - loadingStartedAt
      const delay = Math.max(0, MIN_LOADING_MS - elapsed)
      if (delay > 0) {
        await new Promise((r) => setTimeout(r, delay))
      }
      if (thisRequestId !== requestIdRef.current) return
      hadRecommendationsRef.current = (response.recommendations?.length ?? 0) > 0
      setRecommendations(response.recommendations)
      setMessage(response.message)
      setShowAgentSuggestion(response.show_agent_suggestion || false)
      setAgentName(response.agent_name || '苏童童')
      // 缓存推荐结果
      const cacheKey = `recommendation_results_${searchQuery}`
      sessionStorage.setItem(cacheKey, JSON.stringify({
        recommendations: response.recommendations,
        message: response.message,
        show_agent_suggestion: response.show_agent_suggestion || false,
        agent_name: response.agent_name || '苏童童',
        timestamp: Date.now()
      }))
    } catch (error: any) {
      if (error.name === 'CanceledError' || error.name === 'AbortError') return
      if (thisRequestId !== requestIdRef.current) return
      const elapsed = Date.now() - loadingStartedAt
      const delay = Math.max(0, MIN_LOADING_MS - elapsed)
      if (delay > 0) await new Promise((r) => setTimeout(r, delay))
      if (thisRequestId !== requestIdRef.current) return
      if (!hadList) {
        const errorMsg = error.response?.data?.detail || error.message || '加载失败'
        setMessage('加载失败，请稍后重试')
        setShowAgentSuggestion(false)
        showToast(`加载失败: ${errorMsg}`, 'error')
      }
    } finally {
      if (thisRequestId === requestIdRef.current) {
        setIsLoading(false)
      }
      if (abortRef.current?.signal === signal) abortRef.current = null
    }
  }

  const handleRemoveCard = (bookId: number) => {
    setRecommendations((prev) => prev.filter((item) => item.book_id !== bookId))
  }

  const handleViewDetails = async (bookId: number) => {
    try {
      const book = await booksAPI.getBook(bookId)
      setSelectedBook(book)
      setIsDetailModalOpen(true)
    } catch (error: any) {
      console.error('获取书籍详情失败:', error)
      showToast('获取书籍详情失败，请稍后重试', 'error')
    }
  }

  const handleAskAgent = (bookId: number, bookTitle?: string) => {
    setSelectedBookId(bookId)
    setSelectedBookTitleForAsk(bookTitle ?? null)
    setIsAgentModalOpen(true)
  }

  return (
    <div className="min-h-screen pb-20">
      {/* 返回按钮 */}
      <div className="mb-6">
        <button
          onClick={() => navigate('/')}
          className="flex items-center space-x-2 text-foreground/70 hover:text-foreground transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
          <span>返回首页</span>
        </button>
      </div>

      {/* 搜索查询显示 */}
      {query && (
        <div className="mb-8 flex items-center justify-between">
          <h1 className="text-2xl font-semibold text-foreground mb-2">
            为你推荐：<span className="text-purple-500">"{query}"</span>
          </h1>
          {recommendations.length > 0 && (
            <button
              onClick={() => loadRecommendations(query, true)}
              disabled={isLoading}
              className="flex items-center gap-2 px-4 py-2 rounded-full bg-card border border-border hover:bg-background transition-all text-sm hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed text-purple-600 dark:text-purple-400 min-w-[100px]"
              title="换一批推荐"
            >
              <RefreshCw className={`w-4 h-4 flex-shrink-0 ${isLoading ? 'animate-spin' : ''}`} />
              <span>{isLoading ? '换一批中...' : '换一批'}</span>
            </button>
          )}
        </div>
      )}

      {/* 加载状态：仅首次加载时全屏 spinner，换一批时保留列表并显示遮罩 */}
      {isLoading && recommendations.length === 0 && (
        <LoadingSpinner
          message="正在为你寻找合适的书籍，这可能需要10-15秒..."
          fullScreen={false}
          showEmotionTip={true}
        />
      )}

      {/* 消息提示（有推荐结果时显示，避免与空状态冲突） */}
      {!isLoading && message && recommendations.length > 0 && (
        <div className="text-center mb-8">
          <p className="text-foreground/70 italic mb-4">{message}</p>
          {showAgentSuggestion && (
            <button
              onClick={() => {
                setIsAgentModalOpen(true)
                setSelectedBookId(null)
                setSelectedBookTitleForAsk(null)
              }}
              className="px-6 py-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-xl hover:opacity-90 transition-all text-base font-medium shadow-lg"
            >
              去聊聊
            </button>
          )}
        </div>
      )}

      {/* 推荐结果：换一批时保留列表并叠加半透明遮罩（z-10 保证在列表上方） */}
      {recommendations.length > 0 && (
        <div className="relative min-h-[200px]">
          <div className={`space-y-6 transition-opacity duration-200 ${isLoading ? 'opacity-50' : ''}`}>
            {recommendations.map((item) => (
              <RecommendationCard
                key={item.book_id}
                item={item}
                onRemove={handleRemoveCard}
                onViewDetails={handleViewDetails}
                onAskAgent={handleAskAgent}
              />
            ))}
          </div>
          {isLoading && (
            <div className="fixed inset-0 z-[100] flex items-center justify-center bg-background/50 backdrop-blur-sm pointer-events-none">
              <div className="flex flex-col items-center gap-4 text-foreground bg-card px-8 py-6 rounded-xl shadow-xl border border-border max-w-[280px]">
                <RefreshCw className="w-10 h-10 animate-spin text-purple-500 flex-shrink-0" />
                <span className="text-sm font-medium">正在换一批...</span>
                <p className="text-xs text-foreground/70 text-center leading-relaxed">
                  {refreshCareTip}
                </p>
                <div className="flex gap-1.5">
                  <span className="w-2 h-2 rounded-full bg-purple-500 animate-bounce" style={{ animationDelay: '0ms' }} />
                  <span className="w-2 h-2 rounded-full bg-purple-500 animate-bounce" style={{ animationDelay: '150ms' }} />
                  <span className="w-2 h-2 rounded-full bg-purple-500 animate-bounce" style={{ animationDelay: '300ms' }} />
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* 用户将本批推荐全部标记为不感兴趣 */}
      {!isLoading && recommendations.length === 0 && hadRecommendationsRef.current && query && (
        <EmptyState
          message="本批推荐都已标记为不感兴趣"
          description="换一批看看有没有更符合心意的？"
          actionLabel="换一批推荐"
          onAction={() => loadRecommendations(query, true)}
          secondaryLabel="返回首页"
          onSecondary={() => navigate('/')}
        />
      )}

      {/* API 返回空结果（未找到相关书籍） */}
      {!isLoading && recommendations.length === 0 && !hadRecommendationsRef.current && (
        <EmptyState
          message="未找到相关书籍"
          description="换个心情或关键词再试一次吧"
          actionLabel="返回首页重新搜索"
          onAction={() => navigate('/')}
        />
      )}

      {/* 详情模态窗 */}
      <BookDetailModal
        book={selectedBook}
        isOpen={isDetailModalOpen}
        onClose={() => setIsDetailModalOpen(false)}
        onAskAgent={handleAskAgent}
      />

      {/* AI 书童对话模态窗 */}
      <AgentChatModal
        bookId={selectedBookId}
        isOpen={isAgentModalOpen}
        onClose={() => {
          setIsAgentModalOpen(false)
          setSelectedBookId(null)
          setSelectedBookTitleForAsk(null)
        }}
        initialSessionName={selectedBookTitleForAsk}
        initialQuestion={selectedBookTitleForAsk ? `《${selectedBookTitleForAsk}》这本书讲了什么` : undefined}
      />
    </div>
  )
}
