import { useState, useEffect } from 'react'
import { TrendingUp } from 'lucide-react'
import { Book } from '../api/books'
import { popularAPI } from '../api/popular'
import BookDetailModal from '../components/BookDetailModal'
import UnifiedSearch from '../components/UnifiedSearch'

export default function SearchPage() {
  const [books, setBooks] = useState<Book[]>([])
  const [popularBooks, setPopularBooks] = useState<Book[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [selectedBook, setSelectedBook] = useState<Book | null>(null)
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false)

  useEffect(() => {
    // 加载"大家都在看"
    loadPopularBooks()
  }, [])

  const handleViewDetails = (book: Book) => {
    setSelectedBook(book)
    setIsDetailModalOpen(true)
  }

  const loadPopularBooks = async () => {
    try {
      const books = await popularAPI.getEveryoneWatching(12)
      setPopularBooks(books)
    } catch (error) {
      console.error('加载热门书籍失败:', error)
    }
  }

  return (
    <div className="space-y-8">
      <div className="text-center space-y-4">
        <h1 className="text-3xl font-bold bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
          全功能检索
        </h1>
        <UnifiedSearch
          onSearchResults={(results) => {
            setBooks(results)
          }}
          setIsLoading={setIsLoading}
        />
      </div>

      {/* 大家都在看 */}
      {popularBooks.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center space-x-2">
            <TrendingUp className="w-5 h-5 text-purple-500" />
            <h2 className="text-xl font-semibold text-foreground">大家都在看</h2>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
            {popularBooks.map((book) => (
              <div
                key={book.id}
                onClick={() => handleViewDetails(book)}
                className="bg-card border border-border rounded-lg p-3 hover:shadow-lg transition-all cursor-pointer hover:scale-105"
              >
                <div className="w-full aspect-[2/3] rounded mb-2 bg-background border border-border flex items-center justify-center overflow-hidden">
                  {book.cover_url ? (
                    <img
                      src={book.cover_url}
                      alt={book.title}
                      className="w-full h-full object-cover"
                      loading="lazy"
                      decoding="async"
                    />
                  ) : (
                    <div className="text-center p-2">
                      <div className="text-sm font-semibold text-foreground/30 mb-1 line-clamp-2">
                        {book.title.length > 8 ? book.title.substring(0, 8) + '...' : book.title}
                      </div>
                      <div className="text-xs text-foreground/20">暂无封面</div>
                    </div>
                  )}
                </div>
                <h3 className="text-sm font-medium text-foreground truncate mb-1">
                  {book.title}
                </h3>
                <p className="text-xs text-foreground/60 truncate">{book.author}</p>
                {book.rating && (
                  <p className="text-xs text-purple-500 mt-1">⭐ {book.rating.toFixed(1)}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 精确搜索 */}
      {books.length > 0 && (
        <div className="space-y-4">
          <h2 className="text-xl font-semibold text-foreground">搜索结果</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {books.map((book) => (
              <div
                key={book.id}
                onClick={() => handleViewDetails(book)}
                className="bg-card border border-border rounded-lg p-4 hover:shadow-lg transition-shadow cursor-pointer"
              >
                <div className="w-full h-48 rounded-lg mb-3 bg-background border border-border flex items-center justify-center overflow-hidden">
                  {book.cover_url ? (
                    <img
                      src={book.cover_url}
                      alt={book.title}
                      className="w-full h-full object-cover"
                      loading="lazy"
                      decoding="async"
                    />
                  ) : (
                    <div className="text-center p-4">
                      <div className="text-2xl font-semibold text-foreground/30 mb-2 line-clamp-2">
                        {book.title.length > 10 ? book.title.substring(0, 10) + '...' : book.title}
                      </div>
                      <div className="text-xs text-foreground/20">暂无封面</div>
                    </div>
                  )}
                </div>
                <h3 className="font-semibold text-foreground mb-1">{book.title}</h3>
                <p className="text-sm text-foreground/70">{book.author}</p>
                {book.rating && (
                  <p className="text-sm text-foreground/60 mt-1">评分：{book.rating.toFixed(1)}</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {books.length === 0 && !isLoading && (
        <div className="text-center text-foreground/60 py-12">
          未找到相关书籍
        </div>
      )}

      {/* 详情模态窗 */}
      <BookDetailModal
        book={selectedBook}
        isOpen={isDetailModalOpen}
        onClose={() => setIsDetailModalOpen(false)}
        onAskAgent={() => {}}
      />
    </div>
  )
}
