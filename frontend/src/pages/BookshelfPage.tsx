import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { bookshelfAPI, BookshelfItem, BookshelfStatus } from '../api/bookshelf'
import BookDetailModal from '../components/BookDetailModal'
import { Book } from '../api/books'
import { booksAPI } from '../api/books'
import { PenSquare, ArrowLeft } from 'lucide-react'
import ConfirmDialog from '../components/ConfirmDialog'

const STATUS_LABELS: Record<BookshelfStatus, string> = {
  to_read: '想读',
  reading: '在读',
  read: '已读',
  dropped: '弃读',
}

export default function BookshelfPage() {
  const navigate = useNavigate()
  const [bookshelves, setBookshelves] = useState<BookshelfItem[]>([])
  const [selectedStatus, setSelectedStatus] = useState<BookshelfStatus | undefined>(undefined)
  const [isLoading, setIsLoading] = useState(false)
  const [selectedBook, setSelectedBook] = useState<Book | null>(null)
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false)
  const [showNoteDialog, setShowNoteDialog] = useState(false)
  const [removeConfirm, setRemoveConfirm] = useState<{
    open: boolean
    id: number | null
    status: BookshelfStatus | null
  }>({ open: false, id: null, status: null })

  /** 返回上一页：如果有历史记录则返回，否则返回首页 */
  const handleGoBack = () => {
    // 检查是否有历史记录可以返回（history.length > 1 表示有上一页）
    if (window.history.length > 1) {
      // 使用 navigate(-1) 返回上一页，这样会保持之前的搜索结果
      navigate(-1)
    } else {
      // 如果没有历史记录，返回首页
      navigate('/')
    }
  }

  useEffect(() => {
    document.title = '阅心 - 心灵驿站'
    return () => { document.title = '阅心' }
  }, [])
  useEffect(() => {
    loadBookshelf()
  }, [selectedStatus])

  const loadBookshelf = async () => {
    setIsLoading(true)
    try {
      const data = await bookshelfAPI.getBookshelf(selectedStatus)
      setBookshelves(data)
    } catch (error) {
      console.error('加载书架失败:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const handleViewDetails = async (bookId: number) => {
    try {
      const book = await booksAPI.getBook(bookId)
      setSelectedBook(book)
      setIsDetailModalOpen(true)
    } catch (error) {
      console.error('获取书籍详情失败:', error)
    }
  }

  /** 打开移除确认弹窗（非弃读=移入弃读，弃读=彻底删除） */
  const openRemoveConfirm = (id: number, currentStatus: BookshelfStatus) => {
    setRemoveConfirm({ open: true, id, status: currentStatus })
  }

  /** 确认移除：非弃读时移入弃读，弃读时从书架彻底删除 */
  const handleConfirmRemove = async () => {
    const { id, status } = removeConfirm
    if (id == null || status == null) return
    setRemoveConfirm({ open: false, id: null, status: null })
    if (status === 'dropped') {
      try {
        await bookshelfAPI.removeFromBookshelf(id)
        loadBookshelf()
      } catch (error) {
        console.error('移除失败:', error)
      }
    } else {
      try {
        await bookshelfAPI.updateBookshelf(id, { status: 'dropped' })
        loadBookshelf()
      } catch (error) {
        console.error('移入弃读失败:', error)
      }
    }
  }

  const booksByStatus = bookshelves.reduce((acc, item) => {
    if (!acc[item.status]) {
      acc[item.status] = []
    }
    acc[item.status].push(item)
    return acc
  }, {} as Record<BookshelfStatus, BookshelfItem[]>)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <button
          onClick={handleGoBack}
          className="flex items-center space-x-3 group cursor-pointer hover:opacity-80 transition-opacity"
          title="返回"
        >
          <div className="flex items-center justify-center w-9 h-9 rounded-lg group-hover:bg-background transition-colors text-foreground">
            <ArrowLeft className="w-5 h-5" />
          </div>
          <h1 className="text-2xl font-bold text-foreground group-hover:opacity-80 transition-opacity">心灵驿站</h1>
        </button>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setSelectedStatus(undefined)}
            className={`px-4 py-2 rounded-lg text-sm ${
              selectedStatus === undefined
                ? 'bg-foreground text-background'
                : 'bg-card border border-border hover:bg-background'
            }`}
          >
            全部
          </button>
          {(Object.keys(STATUS_LABELS) as BookshelfStatus[]).map((status) => (
            <button
              key={status}
              onClick={() => setSelectedStatus(status)}
              className={`px-4 py-2 rounded-lg text-sm ${
                selectedStatus === status
                  ? 'bg-foreground text-background'
                  : 'bg-card border border-border hover:bg-background'
              }`}
            >
              {STATUS_LABELS[status]}
            </button>
          ))}
        </div>
      </div>

      {isLoading ? (
        <div className="text-center text-foreground/60 py-12">加载中...</div>
      ) : bookshelves.length === 0 ? (
        <div className="bg-card border border-border rounded-xl p-10 text-center max-w-md mx-auto">
          <p className="text-foreground/80 mb-2">
            {selectedStatus ? `${STATUS_LABELS[selectedStatus]}书架还是空的` : '这里还没有书哦'}
          </p>
          <p className="text-foreground/60 text-sm mb-6">
            去首页发现好书，或搜一搜书名、作者，把想读的加入心灵驿站吧
          </p>
          <div className="flex flex-wrap justify-center gap-3">
            <Link
              to="/"
              className="px-5 py-2.5 rounded-lg bg-foreground text-background hover:opacity-90 transition-opacity text-sm font-medium"
            >
              去逛逛
            </Link>
            <Link
              to="/"
              className="px-5 py-2.5 rounded-lg border border-border hover:bg-background transition-colors text-sm font-medium"
            >
              去搜索
            </Link>
          </div>
        </div>
      ) : (
        <div className="space-y-8">
          {selectedStatus ? (
            <div>
              <h2 className="text-lg font-semibold text-foreground mb-4">
                {STATUS_LABELS[selectedStatus]} ({bookshelves.length})
              </h2>
              <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                {bookshelves.map((item) => (
                  <div
                    key={item.id}
                    className="bg-card border border-border rounded-lg p-3 hover:shadow-lg transition-shadow cursor-pointer relative group"
                    onClick={() => handleViewDetails(item.book.id)}
                  >
                    <div className="w-full aspect-[2/3] rounded mb-2 bg-background border border-border flex items-center justify-center overflow-hidden relative">
                      {item.book.cover_url ? (
                        <img
                          src={item.book.cover_url}
                          alt={item.book.title}
                          className="w-full h-full object-cover"
                          loading="lazy"
                          decoding="async"
                        />
                      ) : (
                        <div className="text-center p-2">
                          <div className="text-xs font-semibold text-foreground/30 mb-1 line-clamp-2">
                            {item.book.title.length > 8 ? item.book.title.substring(0, 8) + '...' : item.book.title}
                          </div>
                          <div className="text-[10px] text-foreground/20">暂无封面</div>
                        </div>
                      )}
                      {/* 悬浮时显示记笔记按钮 - 居中显示在书籍封面上 */}
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          setShowNoteDialog(true)
                        }}
                        className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 px-3 py-1.5 bg-purple-500 text-white rounded-lg opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1.5 text-xs font-medium shadow-lg hover:bg-purple-600 z-10"
                        title="记笔记"
                      >
                        <PenSquare className="w-3.5 h-3.5" />
                        <span>记笔记</span>
                      </button>
                    </div>
                    <h3 className="text-sm font-medium text-foreground truncate">
                      {item.book.title}
                    </h3>
                    <p className="text-xs text-foreground/60 truncate">{item.book.author}</p>
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        openRemoveConfirm(item.id, item.status)
                      }}
                      className="absolute top-2 right-2 p-1 bg-black/50 rounded-full opacity-0 group-hover:opacity-100 transition-opacity z-10"
                      title={item.status === 'dropped' ? '从书架移除' : '移入弃读'}
                    >
                      <span className="text-white text-xs">×</span>
                    </button>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            (Object.keys(STATUS_LABELS) as BookshelfStatus[]).map((status) => {
              const items = booksByStatus[status] || []
              if (items.length === 0) return null

              return (
                <div key={status}>
                  <h2 className="text-lg font-semibold text-foreground mb-4">
                    {STATUS_LABELS[status]} ({items.length})
                  </h2>
                  <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
                    {items.map((item) => (
                      <div
                        key={item.id}
                        className="bg-card border border-border rounded-lg p-3 hover:shadow-lg transition-shadow cursor-pointer relative group"
                        onClick={() => handleViewDetails(item.book.id)}
                      >
                        <div className="w-full aspect-[2/3] rounded mb-2 bg-background border border-border flex items-center justify-center overflow-hidden relative">
                          {item.book.cover_url ? (
                            <img
                              src={item.book.cover_url}
                              alt={item.book.title}
                              className="w-full h-full object-cover"
                              loading="lazy"
                              decoding="async"
                            />
                          ) : (
                            <div className="text-center p-2">
                              <div className="text-xs font-semibold text-foreground/30 mb-1 line-clamp-2">
                                {item.book.title.length > 8 ? item.book.title.substring(0, 8) + '...' : item.book.title}
                              </div>
                              <div className="text-[10px] text-foreground/20">暂无封面</div>
                            </div>
                          )}
                          {/* 悬浮时显示记笔记按钮 - 居中显示在书籍封面上 */}
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              setShowNoteDialog(true)
                            }}
                            className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 px-3 py-1.5 bg-purple-500 text-white rounded-lg opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1.5 text-xs font-medium shadow-lg hover:bg-purple-600 z-10"
                            title="记笔记"
                          >
                            <PenSquare className="w-3.5 h-3.5" />
                            <span>记笔记</span>
                          </button>
                        </div>
                        <h3 className="text-sm font-medium text-foreground truncate">
                          {item.book.title}
                        </h3>
                        <p className="text-xs text-foreground/60 truncate">{item.book.author}</p>
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            openRemoveConfirm(item.id, item.status)
                          }}
                          className="absolute top-2 right-2 p-1 bg-black/50 rounded-full opacity-0 group-hover:opacity-100 transition-opacity z-10"
                          title={item.status === 'dropped' ? '从书架移除' : '移入弃读'}
                        >
                          <span className="text-white text-xs">×</span>
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )
            })
          )}
        </div>
      )}


      {/* 详情模态窗 */}
      <BookDetailModal
        book={selectedBook}
        isOpen={isDetailModalOpen}
        onClose={() => setIsDetailModalOpen(false)}
        onAskAgent={() => {}}
      />

      {/* 笔记功能提示弹窗 */}
      <ConfirmDialog
        isOpen={showNoteDialog}
        title="笔记功能"
        message="此刻还不能记录下你这一路的流离哦～请耐心等待笔记功能上线啦"
        confirmText="知道了"
        cancelText=""
        onConfirm={() => setShowNoteDialog(false)}
        onCancel={() => setShowNoteDialog(false)}
        showCancel={false}
      />

      {/* 移除/移入弃读 二次确认弹窗 */}
      <ConfirmDialog
        isOpen={removeConfirm.open}
        title={removeConfirm.status === 'dropped' ? '从书架移除' : '移入弃读'}
        message={
          removeConfirm.status === 'dropped'
            ? '确定要从书架彻底移除这本书吗？'
            : '确定要将此书移入「弃读」？'
        }
        confirmText="确定"
        cancelText="取消"
        onConfirm={handleConfirmRemove}
        onCancel={() => setRemoveConfirm({ open: false, id: null, status: null })}
        showCancel={true}
      />
    </div>
  )
}
