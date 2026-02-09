import { useState, useEffect, useRef } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { searchAPI } from '../api/search'
import { bookshelfAPI } from '../api/bookshelf'
import { Book } from '../api/books'
import BookDetailModal from '../components/BookDetailModal'
import AgentChatModal from '../components/AgentChatModal'
import LoadingSpinner from '../components/LoadingSpinner'
import EmptyState from '../components/EmptyState'
import { showToast } from '../components/ToastContainer'
import ConfirmDialog from '../components/ConfirmDialog'
import { ArrowLeft, X } from 'lucide-react'
import { booksAPI } from '../api/books'
import { highlightText } from '../utils/highlight'

export default function SearchResultsPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const query = searchParams.get('q') || ''

  const [books, setBooks] = useState<Book[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [selectedBook, setSelectedBook] = useState<Book | null>(null)
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false)
  const [isAgentModalOpen, setIsAgentModalOpen] = useState(false)
  const [selectedBookId, setSelectedBookId] = useState<number | null>(null)
  const [selectedBookTitleForAsk, setSelectedBookTitleForAsk] = useState<string | null>(null)
  const [notInterestedBook, setNotInterestedBook] = useState<{ id: number; title: string } | null>(null)
  const [retryKey, _setRetryKey] = useState(0)
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => {
    document.title = query ? `阅心 - 搜索：${query}` : '阅心 - 搜索'
    return () => { document.title = '阅心' }
  }, [query])
  useEffect(() => {
    if (!query) {
      setIsLoading(false)
      return
    }
    
    // 检查缓存：如果查询参数相同，直接使用缓存的结果
    const cacheKey = `search_results_${query}`
    const cachedData = sessionStorage.getItem(cacheKey)
    if (cachedData) {
      try {
        const cached = JSON.parse(cachedData)
        // 检查缓存是否过期（5分钟内有效）
        if (Date.now() - cached.timestamp < 5 * 60 * 1000) {
          setBooks(cached.books)
          setIsLoading(false)
          return
        }
      } catch (e) {
        // 缓存解析失败，继续正常搜索
      }
    }
    
    if (abortRef.current) abortRef.current.abort()
    abortRef.current = new AbortController()
    const signal = abortRef.current.signal
    let cancelled = false
    const load = async () => {
      setIsLoading(true)
      try {
        const results = await searchAPI.exactSearch({ title: query, author: query }, signal)
        if (signal.aborted || cancelled) return
        setBooks(results)
        // 缓存搜索结果
        sessionStorage.setItem(cacheKey, JSON.stringify({
          books: results,
          timestamp: Date.now()
        }))
        if (results.length === 0) showToast('未找到相关书籍', 'error')
      } catch (error: any) {
        if (error.name === 'CanceledError' || error.name === 'AbortError') return
        if (cancelled) return
        const errorMsg = error.response?.data?.detail || error.message || '搜索失败'
        setBooks([])
        showToast(`搜索失败: ${errorMsg}`, 'error')
      } finally {
        if (!cancelled) setIsLoading(false)
      }
    }
    load()
    return () => {
      cancelled = true
      if (abortRef.current) abortRef.current.abort()
    }
  }, [query, retryKey])

  const handleNotInterested = async (e: React.MouseEvent, bookId: number, bookTitle: string) => {
    e.stopPropagation()
    setNotInterestedBook({ id: bookId, title: bookTitle })
  }

  const confirmNotInterested = async () => {
    if (!notInterestedBook) return
    
    try {
      await bookshelfAPI.markNotInterested(notInterestedBook.id)
      setBooks((prev) => prev.filter((b) => b.id !== notInterestedBook.id))
      showToast('已标记为不感兴趣', 'success')
    } catch (error: any) {
      console.error('标记不感兴趣失败:', error)
      showToast('操作失败，请稍后重试', 'error')
    } finally {
      setNotInterestedBook(null)
    }
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
      <div className="mb-6">
        <button
          onClick={() => navigate('/')}
          className="flex items-center space-x-2 text-foreground/70 hover:text-foreground transition-colors"
        >
          <ArrowLeft className="w-5 h-5" />
          <span>返回首页</span>
        </button>
      </div>

      {query && (
        <div className="mb-8">
          <h1 className="text-2xl font-semibold text-foreground mb-2">
            搜索结果：<span className="text-purple-500">"{query}"</span>
          </h1>
        </div>
      )}

      {isLoading && (
        <LoadingSpinner message="正在搜索..." fullScreen={false} showEmotionTip={false} />
      )}

      {!isLoading && books.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {books.map((book) => (
            <div
              key={book.id}
              className="relative bg-card border border-border rounded-lg p-4 hover:shadow-lg transition-all cursor-pointer hover:scale-[1.02] group flex gap-4"
            >
              <button
                onClick={(e) => handleNotInterested(e, book.id, book.title)}
                className="absolute top-2 right-2 p-1.5 rounded-full hover:bg-background transition-colors z-10"
                title="不感兴趣"
              >
                <X className="w-4 h-4 text-foreground/60" />
              </button>
              <div
                onClick={() => handleViewDetails(book.id)}
                className="flex gap-4 flex-1 min-w-0"
              >
                <div className="w-20 h-28 flex-shrink-0 rounded bg-background border border-border flex items-center justify-center overflow-hidden">
                  {book.cover_url ? (
                    <img
                      src={book.cover_url}
                      alt={book.title}
                      className="w-full h-full object-cover group-hover:brightness-110 transition-all"
                      loading="lazy"
                      decoding="async"
                    />
                  ) : (
                    <div className="text-center p-2">
                      <div className="text-xs font-semibold text-foreground/30 mb-1 line-clamp-2">
                        {book.title.length > 8 ? book.title.substring(0, 8) + '...' : book.title}
                      </div>
                      <div className="text-[10px] text-foreground/20">暂无封面</div>
                    </div>
                  )}
                </div>
                <div className="flex-1 min-w-0 flex flex-col">
                  <h3 
                    className="text-base font-semibold text-foreground mb-1 line-clamp-2"
                    dangerouslySetInnerHTML={{ 
                      __html: highlightText(book.title || '', [query]) 
                    }}
                  />
                  <p 
                    className="text-sm text-foreground/60 mb-2"
                    dangerouslySetInnerHTML={{ 
                      __html: highlightText(book.author || '', [query]) 
                    }}
                  />
                  {book.rating != null && book.rating > 0 && (
                    <p className="text-sm text-purple-500 mb-2">⭐ {book.rating.toFixed(1)}</p>
                  )}
                  {book.reason && (
                    <div className="mt-auto pt-2 border-l-2 border-purple-500/50 pl-3 bg-background/50 rounded-r">
                      <p className="text-sm text-foreground/90 leading-relaxed font-medium">
                        {book.reason}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {!isLoading && books.length === 0 && query && (
        <EmptyState
          message="未找到相关书籍"
          description="哎呀！请输入更准确的书名、作者或 ISBN吧～"
          actionLabel="返回首页"
          onAction={() => navigate('/')}
          secondaryLabel="试试语义搜索"
          onSecondary={() => navigate(`/recommendations?q=${encodeURIComponent(query)}`)}
          highlightSecondary={true}
        />
      )}

      <BookDetailModal
        book={selectedBook}
        isOpen={isDetailModalOpen}
        onClose={() => setIsDetailModalOpen(false)}
        onAskAgent={handleAskAgent}
      />

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

      {/* 不感兴趣确认对话框 */}
      <ConfirmDialog
        isOpen={!!notInterestedBook}
        title="不感兴趣"
        message={notInterestedBook ? `确定要将《${notInterestedBook.title}》标记为不感兴趣吗？这将帮助系统更好地为你推荐书籍。` : ''}
        confirmText="确认"
        cancelText="取消"
        onConfirm={confirmNotInterested}
        onCancel={() => setNotInterestedBook(null)}
      />
    </div>
  )
}
