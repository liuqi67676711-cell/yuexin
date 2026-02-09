import { useState, useRef, useEffect } from 'react'
import { X, Send, Bot, Edit2, Plus, Trash2, Menu, ChevronLeft } from 'lucide-react'
import { agentAPI, ChatMessage, ChatSession } from '../api/agent'
import { showToast } from './ToastContainer'
import { formatRelativeTime } from '../utils/relativeTime'
import ChoiceDialog from './ChoiceDialog'

interface AgentChatModalProps {
  bookId: number | null
  isOpen: boolean
  onClose: () => void
  /** 打开时新建会话并自动发送的问题（会话名用 initialSessionName） */
  initialSessionName?: string | null
  initialQuestion?: string | null
}

export default function AgentChatModal({ bookId, isOpen, onClose, initialSessionName, initialQuestion }: AgentChatModalProps) {
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [currentSessionId, setCurrentSessionId] = useState<number | null>(null)
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isEditingName, setIsEditingName] = useState(false)
  const [agentName, setAgentName] = useState('苏童童')
  const [isCreatingSession, setIsCreatingSession] = useState(false)
  const [newSessionName, setNewSessionName] = useState('')
  const [editingSessionId, setEditingSessionId] = useState<number | null>(null)
  const [editingSessionName, setEditingSessionName] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const initialHandledRef = useRef(false)
  const [showChoiceDialog, setShowChoiceDialog] = useState(false)
  const [existingSession, setExistingSession] = useState<ChatSession | null>(null)
  const [pendingBookEntry, setPendingBookEntry] = useState<{
    bookId: number
    sessionName: string
    question: string
  } | null>(null)
  /** 主动关怀：深夜时段（22:00-06:00）打开对话时显示一条问候 */
  const [proactiveCare, setProactiveCare] = useState<string | null>(null)
  /** AI 回复逐步展示：当前正在逐字展示的消息 id、全文、已展示长度 */
  const [streamingMessageId, setStreamingMessageId] = useState<number | null>(null)
  const [streamingFullText, setStreamingFullText] = useState('')
  const [streamingDisplayedLength, setStreamingDisplayedLength] = useState(0)

  const streamingTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  
  // 移动端侧边栏展开/收起状态（移动端默认收起）
  const [isSidebarOpen, setIsSidebarOpen] = useState(false)
  const [isMobile, setIsMobile] = useState(false)
  
  // 检测是否为移动端
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth < 768) // 768px 以下视为移动端
      // 移动端默认收起侧边栏
      if (window.innerWidth < 768) {
        setIsSidebarOpen(false)
      } else {
        setIsSidebarOpen(true)
      }
    }
    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [])
  
  // 逐步展示 AI 回复（约 50 字/秒，缓解等待焦虑）
  useEffect(() => {
    if (streamingMessageId == null || streamingFullText === '') return
    const total = streamingFullText.length
    const step = 2
    streamingTimerRef.current = setInterval(() => {
      setStreamingDisplayedLength((prev) => {
        const next = Math.min(prev + step, total)
        if (next >= total && streamingTimerRef.current) {
          clearInterval(streamingTimerRef.current)
          streamingTimerRef.current = null
          setStreamingMessageId(null)
          setStreamingFullText('')
          setStreamingDisplayedLength(0)
        }
        return next
      })
    }, 40)
    return () => {
      if (streamingTimerRef.current) {
        clearInterval(streamingTimerRef.current)
        streamingTimerRef.current = null
      }
    }
  }, [streamingMessageId, streamingFullText])

  useEffect(() => {
    if (!isOpen) {
      setProactiveCare(null)
      setStreamingMessageId(null)
      setStreamingFullText('')
      setStreamingDisplayedLength(0)
      initialHandledRef.current = false
      setShowChoiceDialog(false)
      setExistingSession(null)
      setPendingBookEntry(null)
      return
    }
    const run = async () => {
      // 1. 先拉取并展示所有历史会话，保证左侧列表始终有内容（含历史对话）
      const isBookEntry = !!(bookId && initialSessionName && initialQuestion && !initialHandledRef.current)
      const loadedSessions = await loadSessions(isBookEntry)
      
      // 2. 若从「这本书讲了什么」进入：检查是否有同名对话
      if (isBookEntry && bookId && initialSessionName && initialQuestion) {
        initialHandledRef.current = true
        
        // 检查是否有同名对话（使用刚加载的sessions）
        const existing = loadedSessions.find(
          (s) => s.name === initialSessionName && s.book_id === bookId
        )
        
        if (existing) {
          // 有同名对话，询问用户是继续聊还是新建
          setExistingSession(existing)
          setPendingBookEntry({ bookId, sessionName: initialSessionName, question: initialQuestion })
          setShowChoiceDialog(true)
        } else {
          // 没有同名对话，直接创建新对话并发送问题
          await createNewBookSession(bookId, initialSessionName, initialQuestion)
        }
      }
    }
    run()
  }, [isOpen, bookId, initialSessionName, initialQuestion])

  // 主动关怀：深夜（22:00-06:00）打开弹窗且非「这本书讲什么」入口时，显示一句问候
  useEffect(() => {
    if (!isOpen || (initialSessionName && initialQuestion)) return
    const hour = new Date().getHours()
    if (hour >= 22 || hour < 6) {
      setProactiveCare('夜深了，读点轻松的吧～')
    } else {
      setProactiveCare(null)
    }
  }, [isOpen, initialSessionName, initialQuestion])

  const createNewBookSession = async (bookId: number, sessionName: string, question: string) => {
    try {
      const session = await agentAPI.createSession({
        name: sessionName,
        book_id: bookId,
      })
      // 先将会话加入左侧列表并选中，再发请求（用户先看到新对话，再等回答）
      setSessions((prev) => [session, ...prev])
      setCurrentSessionId(session.id)
      setMessages([
        {
          id: 0,
          role: 'user',
          content: question,
          created_at: new Date().toISOString(),
          book_id: bookId,
        },
      ])
      setIsLoading(true)
      const res = await agentAPI.chat({
        message: question,
        session_id: session.id,
        book_id: bookId,
      })
      if (res.used_fallback) {
        showToast('当前为简要回复，未使用 DeepSeek。请检查 backend/.env 中的 DEEPSEEK_API_KEY 或到 platform.deepseek.com 充值后重试。', 'error')
      }
      setMessages((prev) => [
        ...prev,
        {
          id: res.message_id,
          role: 'agent',
          content: res.response,
          created_at: new Date().toISOString(),
          book_id: bookId,
        },
      ])
      setStreamingMessageId(res.message_id)
      setStreamingFullText(res.response)
      setStreamingDisplayedLength(0)
    } catch (err: any) {
      console.error('自动提问失败:', err)
      showToast(err.response?.data?.detail || '发送失败，请重试', 'error')
      initialHandledRef.current = false
    } finally {
      setIsLoading(false)
    }
  }

  const handleContinueExistingSession = () => {
    if (!existingSession) return
    
    setShowChoiceDialog(false)
    setCurrentSessionId(existingSession.id)
    // 不自动发送问题，直接加载历史消息
    setPendingBookEntry(null)
    setExistingSession(null)
  }

  const handleCreateNewSession = async () => {
    if (!pendingBookEntry) return
    
    setShowChoiceDialog(false)
    const { bookId, sessionName, question } = pendingBookEntry
    await createNewBookSession(bookId, sessionName, question)
    setPendingBookEntry(null)
    setExistingSession(null)
  }

  const handleCancelChoice = () => {
    setShowChoiceDialog(false)
    setPendingBookEntry(null)
    setExistingSession(null)
    initialHandledRef.current = false
  }

  useEffect(() => {
    if (currentSessionId) {
      loadMessages(currentSessionId)
    } else {
      setMessages([])
    }
  }, [currentSessionId])

  // 消息列表变化时滚动到底部
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // 逐字显示时也自动滚动到底部，确保用户始终看到最新内容
  useEffect(() => {
    if (streamingMessageId !== null && streamingDisplayedLength > 0) {
      // 使用 requestAnimationFrame 确保 DOM 更新后再滚动
      requestAnimationFrame(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
      })
    }
  }, [streamingDisplayedLength, streamingMessageId])

  const loadSessions = async (skipCreateDefault = false): Promise<ChatSession[]> => {
    try {
      console.log('加载会话列表...')
      const loadedSessions = await agentAPI.getSessions()
      console.log('会话列表:', loadedSessions)
      setSessions(loadedSessions)

      if (loadedSessions.length === 0) {
        if (!skipCreateDefault) {
          console.log('没有会话，创建默认会话...')
          await createDefaultSession()
          // 重新获取会话列表
          const newSessions = await agentAPI.getSessions()
          setSessions(newSessions)
          return newSessions
        }
        return []
      } else {
        // 有历史会话时先选中最新一条；若随后走「这本书讲了什么」流程会再切到新会话
        console.log('选择会话:', loadedSessions[0].id)
        setCurrentSessionId(loadedSessions[0].id)
        return loadedSessions
      }
    } catch (error: any) {
      console.error('加载会话失败:', error)
      console.error('错误详情:', error.response?.data || error.message)
      if (!skipCreateDefault) {
        try {
          await createDefaultSession()
          const newSessions = await agentAPI.getSessions()
          setSessions(newSessions)
          return newSessions
        } catch (createError: any) {
          console.error('创建默认会话也失败:', createError)
          const errorMsg = createError.response?.data?.detail || createError.message || '未知错误'
          showToast(`无法初始化对话: ${errorMsg}`, 'error')
        }
      }
      return []
    }
  }

  const createDefaultSession = async () => {
    try {
      const defaultName = bookId ? '关于这本书的对话' : '新对话'
      console.log('创建默认会话:', defaultName)
      const session = await agentAPI.createSession({
        name: defaultName,
        book_id: bookId || null,
      })
      console.log('会话创建成功:', session)
      setSessions([session])
      setCurrentSessionId(session.id)
    } catch (error: any) {
      console.error('创建默认会话失败:', error)
      console.error('错误详情:', error.response?.data || error.message)
      throw error  // 重新抛出错误，让调用者处理
    }
  }

  const loadMessages = async (sessionId: number) => {
    try {
      const loadedMessages = await agentAPI.getMessages(sessionId)
      if (loadedMessages.length === 0) {
        // 如果没有历史记录，显示欢迎消息
        setMessages([
          {
            id: 0,
            role: 'agent',
            content: `你好，我是${agentName}！${bookId ? '关于这本书，你想了解什么呢？' : '有什么想聊的吗？'}`,
            created_at: new Date().toISOString(),
            book_id: bookId || null,
          },
        ])
      } else {
        setMessages(loadedMessages)
      }
      setStreamingMessageId(null)
      setStreamingFullText('')
      setStreamingDisplayedLength(0)
    } catch (error: any) {
      console.error('加载消息失败:', error)
      const msg = error?.message || error?.response?.data?.detail || '加载对话记录失败'
      showToast(msg, 'error')
    }
  }

  const handleCreateSession = async () => {
    if (!newSessionName.trim()) {
      showToast('请输入对话名称', 'error')
      return
    }
    
    try {
      const session = await agentAPI.createSession({
        name: newSessionName.trim(),
        book_id: bookId || null,
      })
      setSessions([session, ...sessions])
      setCurrentSessionId(session.id)
      setNewSessionName('')
      setIsCreatingSession(false)
      // 移动端：创建会话后自动关闭侧边栏
      if (isMobile) {
        setIsSidebarOpen(false)
      }
      showToast('对话已创建', 'success')
    } catch (error: any) {
      console.error('创建会话失败:', error)
      showToast('创建失败，请稍后重试', 'error')
    }
  }

  const handleUpdateSessionName = async (sessionId: number) => {
    if (!editingSessionName.trim()) {
      showToast('请输入对话名称', 'error')
      return
    }
    
    try {
      const updated = await agentAPI.updateSession(sessionId, {
        name: editingSessionName.trim(),
      })
      setSessions(sessions.map(s => s.id === sessionId ? updated : s))
      setEditingSessionId(null)
      setEditingSessionName('')
      showToast('对话名称已更新', 'success')
    } catch (error: any) {
      console.error('更新会话名称失败:', error)
      showToast('更新失败，请稍后重试', 'error')
    }
  }

  const handleDeleteSession = async (sessionId: number) => {
    try {
      await agentAPI.deleteSession(sessionId)
      setSessions(sessions.filter(s => s.id !== sessionId))
      if (currentSessionId === sessionId) {
        // 如果删除的是当前会话，选择第一个会话或创建新会话
        const remaining = sessions.filter(s => s.id !== sessionId)
        if (remaining.length > 0) {
          setCurrentSessionId(remaining[0].id)
        } else {
          setCurrentSessionId(null)
          await createDefaultSession()
        }
      }
      showToast('对话已删除', 'success')
    } catch (error: any) {
      console.error('删除会话失败:', error)
      showToast('删除失败，请稍后重试', 'error')
    }
  }

  const handleSend = async () => {
    if (!input.trim() || isLoading) {
      if (!currentSessionId) {
        alert('对话未初始化，请稍候...')
        // 尝试重新创建会话
        await createDefaultSession()
      }
      return
    }

    const userMessage = input.trim()
    setInput('')
    setProactiveCare(null) // 用户发送后不再显示主动关怀

    // 如果还没有会话ID，先创建
    let sessionId = currentSessionId
    if (!sessionId) {
      try {
        const defaultName = bookId ? '关于这本书的对话' : '新对话'
        const session = await agentAPI.createSession({
          name: defaultName,
          book_id: bookId || null,
        })
        setSessions([session, ...sessions])
        setCurrentSessionId(session.id)
        sessionId = session.id
      } catch (error: any) {
        console.error('创建会话失败:', error)
        const errorMsg = error.response?.data?.detail || error.message || '网络错误'
        showToast(`创建对话失败: ${errorMsg}`, 'error')
        return
      }
    }
    
    // 立即显示用户消息（乐观更新）
    const tempUserMessage: ChatMessage = {
      id: Date.now(),
      role: 'user',
      content: userMessage,
      created_at: new Date().toISOString(),
      book_id: bookId || null,
    }
    setMessages((prev) => [...prev, tempUserMessage])
    setIsLoading(true)

    try {
      const response = await agentAPI.chat({
        message: userMessage,
        session_id: sessionId!,
        book_id: bookId || undefined,
      })
      if (response.used_fallback) {
        showToast('当前为简要回复，未使用 DeepSeek。请检查 DEEPSEEK_API_KEY 或到 platform.deepseek.com 充值后重试。', 'error')
      }
      // 替换临时消息并添加AI回复
      setMessages((prev) => {
        const filtered = prev.filter((msg) => msg.id !== tempUserMessage.id)
        return [
          ...filtered,
          {
            id: response.message_id - 1,
            role: 'user',
            content: userMessage,
            created_at: new Date().toISOString(),
            book_id: bookId || null,
          },
          {
            id: response.message_id,
            role: 'agent',
            content: response.response,
            created_at: new Date().toISOString(),
            book_id: bookId || null,
          },
        ]
      })
      setStreamingMessageId(response.message_id)
      setStreamingFullText(response.response)
      setStreamingDisplayedLength(0)
      // 更新会话列表（不重载本会话消息，保留逐步展示效果）
      await loadSessions()
    } catch (error: any) {
      console.error('发送消息失败:', error)
      const errorMsg = error.response?.data?.detail || error.message || '网络错误'
      showToast(`发送失败: ${errorMsg}`, 'error')
      setMessages((prev) => {
        const filtered = prev.filter((msg) => msg.id !== tempUserMessage.id)
        return [
          ...filtered,
          {
            id: Date.now(),
            role: 'agent',
            content: '抱歉，我暂时无法回复，请稍后再试。',
            created_at: new Date().toISOString(),
            book_id: bookId || null,
          },
        ]
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleSaveAgentName = async () => {
    if (!agentName.trim()) {
      showToast('书童名称不能为空', 'error')
      return
    }
    
    // 直接更新本地状态，因为不需要后端保存
    setAgentName(agentName.trim())
    setIsEditingName(false)
    showToast('书童名称已更新', 'success')
  }

  const currentSession = sessions.find(s => s.id === currentSessionId)

  const handleClose = () => {
    if (currentSessionId != null && messages.length >= 2) {
      agentAPI.summarizeSession(currentSessionId).catch(() => {})
    }
    onClose()
  }

  if (!isOpen) return null

  const handleBackdropClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) {
      handleClose()
    }
  }

  return (
    <div 
      className="fixed inset-0 z-[9999] flex items-center justify-center p-2 md:p-4 bg-black/50 backdrop-blur-sm"
      onClick={handleBackdropClick}
    >
      <div 
        className="bg-card border border-border rounded-xl w-full max-w-4xl h-[90vh] md:h-[85vh] flex flex-col shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* 头部 */}
        <div className="px-4 md:px-6 py-4 border-b border-border flex items-center justify-between">
          <div className="flex items-center space-x-3 flex-1 min-w-0">
            {/* 移动端：侧边栏切换按钮 */}
            {isMobile && (
              <button
                onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                className="p-2 rounded-full hover:bg-background transition-colors flex-shrink-0"
                title={isSidebarOpen ? "收起对话列表" : "展开对话列表"}
              >
                {isSidebarOpen ? (
                  <ChevronLeft className="w-5 h-5 text-foreground" />
                ) : (
                  <Menu className="w-5 h-5 text-foreground" />
                )}
              </button>
            )}
            <Bot className="w-5 h-5 text-foreground flex-shrink-0" />
            {isEditingName ? (
              <div className="flex items-center space-x-2 flex-1 min-w-0">
                <input
                  type="text"
                  value={agentName}
                  onChange={(e) => setAgentName(e.target.value)}
                  onKeyPress={(e) => {
                    if (e.key === 'Enter') handleSaveAgentName()
                    if (e.key === 'Escape') {
                      setIsEditingName(false)
                      setAgentName('苏童童')
                    }
                  }}
                  className="flex-1 px-2 py-1 rounded bg-background border border-border text-foreground focus:outline-none focus:ring-2 focus:ring-purple-500/50 min-w-0"
                  autoFocus
                />
                <button
                  onClick={handleSaveAgentName}
                  className="px-3 py-1 text-sm bg-purple-500 text-white rounded hover:opacity-90 flex-shrink-0"
                >
                  保存
                </button>
                <button
                  onClick={() => {
                    setIsEditingName(false)
                    setAgentName('苏童童')
                  }}
                  className="px-3 py-1 text-sm border border-border rounded hover:bg-background flex-shrink-0"
                >
                  取消
                </button>
              </div>
            ) : (
              <>
                <h2 className="text-base md:text-lg font-semibold text-foreground truncate">
                  {agentName} AI 书童
                </h2>
                <button
                  onClick={() => setIsEditingName(true)}
                  className="ml-2 p-1 rounded hover:bg-background transition-colors flex-shrink-0"
                  title="编辑名称"
                >
                  <Edit2 className="w-4 h-4 text-foreground/60" />
                </button>
              </>
            )}
          </div>
          <div className="flex items-center flex-shrink-0">
            <button
              onClick={handleClose}
              className="p-2 rounded-full hover:bg-background transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        <div className="flex flex-1 overflow-hidden relative">
          {/* 移动端遮罩层：侧边栏展开时显示 */}
          {isMobile && isSidebarOpen && (
            <div
              className="absolute inset-0 bg-black/30 z-[5] md:hidden"
              onClick={() => setIsSidebarOpen(false)}
            />
          )}
          
          {/* 会话列表侧边栏 */}
          <div className={`
            absolute md:relative
            top-0 left-0 h-full
            w-64 border-r border-border bg-background/95 md:bg-background/50 
            flex flex-col flex-shrink-0 z-10
            transition-transform duration-300 ease-in-out
            ${isMobile ? (isSidebarOpen ? 'translate-x-0' : '-translate-x-full') : ''}
            ${isMobile ? 'shadow-xl' : ''}
          `}>
              <div className="p-4 border-b border-border">
                <button
                  onClick={() => setIsCreatingSession(true)}
                  className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-purple-500 text-white rounded-lg hover:opacity-90 transition-opacity"
                >
                  <Plus className="w-4 h-4" />
                  <span>新建对话</span>
                </button>
              </div>
              
              {isCreatingSession && (
                <div className="p-4 border-b border-border">
                  <input
                    type="text"
                    value={newSessionName}
                    onChange={(e) => setNewSessionName(e.target.value)}
                    onKeyPress={(e) => {
                      if (e.key === 'Enter') handleCreateSession()
                      if (e.key === 'Escape') {
                        setIsCreatingSession(false)
                        setNewSessionName('')
                      }
                    }}
                    placeholder="输入对话名称..."
                    className="w-full px-3 py-2 rounded bg-card border border-border text-foreground focus:outline-none focus:ring-2 focus:ring-purple-500/50 mb-2"
                    autoFocus
                  />
                  <div className="flex space-x-2">
                    <button
                      onClick={handleCreateSession}
                      className="flex-1 px-3 py-1 text-sm bg-purple-500 text-white rounded hover:opacity-90"
                    >
                      创建
                    </button>
                    <button
                      onClick={() => {
                        setIsCreatingSession(false)
                        setNewSessionName('')
                      }}
                      className="flex-1 px-3 py-1 text-sm border border-border rounded hover:bg-background"
                    >
                      取消
                    </button>
                  </div>
                </div>
              )}

              <div className="flex-1 overflow-y-auto p-2">
                {sessions.map((session) => (
                  <div
                    key={session.id}
                    className={`p-3 rounded-lg mb-2 cursor-pointer transition-colors ${
                      currentSessionId === session.id
                        ? 'bg-purple-500/20 border border-purple-500/50'
                        : 'bg-card border border-border hover:bg-background'
                    }`}
                    onClick={() => {
                      setCurrentSessionId(session.id)
                      // 移动端：选择会话后自动关闭侧边栏
                      if (isMobile) {
                        setIsSidebarOpen(false)
                      }
                    }}
                  >
                    {editingSessionId === session.id ? (
                      <div className="space-y-2">
                        <input
                          type="text"
                          value={editingSessionName}
                          onChange={(e) => setEditingSessionName(e.target.value)}
                          onKeyPress={(e) => {
                            if (e.key === 'Enter') handleUpdateSessionName(session.id)
                            if (e.key === 'Escape') {
                              setEditingSessionId(null)
                              setEditingSessionName('')
                            }
                          }}
                          className="w-full px-2 py-1 text-sm rounded bg-background border border-border text-foreground focus:outline-none focus:ring-2 focus:ring-purple-500/50"
                          autoFocus
                        />
                        <div className="flex space-x-1">
                          <button
                            onClick={() => handleUpdateSessionName(session.id)}
                            className="flex-1 px-2 py-1 text-xs bg-purple-500 text-white rounded hover:opacity-90"
                          >
                            保存
                          </button>
                          <button
                            onClick={() => {
                              setEditingSessionId(null)
                              setEditingSessionName('')
                            }}
                            className="flex-1 px-2 py-1 text-xs border border-border rounded hover:bg-background"
                          >
                            取消
                          </button>
                        </div>
                      </div>
                    ) : (
                      <div className="flex items-center justify-between group">
                        <div className="flex-1 min-w-0">
                          <p className="text-sm font-medium text-foreground truncate">
                            {session.name}
                          </p>
                          <p className="text-xs text-foreground/60 mt-1">
                            {formatRelativeTime(session.updated_at)}
                          </p>
                        </div>
                        <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              setEditingSessionId(session.id)
                              setEditingSessionName(session.name)
                            }}
                            className="p-1 rounded hover:bg-background"
                            title="编辑名称"
                          >
                            <Edit2 className="w-3 h-3 text-foreground/60" />
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation()
                              handleDeleteSession(session.id)
                            }}
                            className="p-1 rounded hover:bg-background"
                            title="删除对话"
                          >
                            <Trash2 className="w-3 h-3 text-red-500" />
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

          {/* 主对话区域 */}
          <div className="flex-1 flex flex-col min-w-0 w-full">
            {/* 当前会话标题 */}
            {currentSession && (
              <div className="px-4 md:px-6 py-2 border-b border-border bg-background/30">
                <p className="text-sm font-medium text-foreground truncate">{currentSession.name}</p>
              </div>
            )}

            {/* 消息列表 */}
            <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-4">
              {messages.length === 0 ? (
                proactiveCare ? (
                  <div className="flex justify-start">
                    <div className="flex items-start space-x-2 max-w-[80%]">
                      <Bot className="w-5 h-5 text-purple-500 mt-1 flex-shrink-0" />
                      <div className="rounded-lg px-4 py-2 bg-background border border-border">
                        <p className="text-sm leading-relaxed">{agentName}：{proactiveCare}</p>
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center text-foreground/60 py-12">
                    <Bot className="w-12 h-12 mx-auto mb-4 opacity-50" />
                    <p>开始与 {agentName} 对话吧</p>
                  </div>
                )
              ) : (
                [...messages]
                  .sort((a, b) => (a.id - b.id) || (new Date(a.created_at).getTime() - new Date(b.created_at).getTime()))
                  .map((msg) => (
                  <div
                    key={`${msg.id}-${msg.role}-${msg.created_at}`}
                    className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'} group`}
                  >
                    <div className="flex items-start space-x-2 max-w-[85%] md:max-w-[80%]">
                      {msg.role === 'agent' && (
                        <Bot className="w-4 h-4 md:w-5 md:h-5 text-purple-500 mt-1 flex-shrink-0" />
                      )}
                      <div
                        className={`rounded-lg px-3 py-2 md:px-4 md:py-2 ${
                          msg.role === 'user'
                            ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white'
                            : 'bg-background border border-border'
                        }`}
                      >
                        <p className="text-xs md:text-sm leading-relaxed whitespace-pre-wrap break-words">
                          {msg.role === 'agent' && streamingMessageId === msg.id ? (
                            <>
                              {streamingFullText.slice(0, streamingDisplayedLength)}
                              {streamingDisplayedLength < streamingFullText.length && (
                                <span className="inline-block w-0.5 h-4 ml-0.5 bg-purple-500 animate-pulse align-middle" aria-hidden />
                              )}
                            </>
                          ) : (
                            msg.content
                          )}
                        </p>
                      </div>
                    </div>
                  </div>
                  ))
              )}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="flex items-center gap-2 bg-background border border-border rounded-lg px-4 py-3 animate-pulse">
                    <Bot className="w-4 h-4 text-purple-500 animate-pulse" />
                    <p className="text-sm text-foreground/60">
                      正在思考
                      <span className="inline-block w-4 text-left animate-thinking-dots">...</span>
                    </p>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* 输入框 */}
            <div className="px-4 md:px-6 py-4 border-t border-border">
              <div className="flex items-center space-x-2">
                <textarea
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder={currentSessionId ? "输入你的问题..." : "正在初始化对话..."}
                  className="flex-1 px-3 md:px-4 py-2 rounded-lg bg-background border border-border text-foreground placeholder-foreground/40 focus:outline-none focus:ring-2 focus:ring-purple-500/50 resize-none text-sm md:text-base"
                  rows={2}
                  disabled={isLoading}
                />
                <button
                  onClick={handleSend}
                  disabled={!input.trim() || isLoading || !currentSessionId}
                  className="p-2 md:p-3 bg-gradient-to-r from-purple-500 to-pink-500 text-white rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed shadow-lg flex-shrink-0"
                >
                  <Send className="w-4 h-4 md:w-5 md:h-5" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 选择对话框：继续聊还是新建对话 */}
      <ChoiceDialog
        isOpen={showChoiceDialog}
        title="发现已有对话"
        message={existingSession ? `发现已有关于《${existingSession.name}》的对话，你想继续之前的对话还是新建一个对话？` : ''}
        primaryText="新建对话"
        secondaryText="继续聊"
        onPrimary={handleCreateNewSession}
        onSecondary={handleContinueExistingSession}
        onCancel={handleCancelChoice}
      />
    </div>
  )
}
