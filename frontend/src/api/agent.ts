import { apiClient } from './client'

export interface ChatMessageRequest {
  message: string
  session_id: number
  book_id?: number
}

export interface ChatResponse {
  response: string
  agent_name: string
  message_id: number
  /** true 表示未走 DeepSeek，使用了内置简单回复（如 402 或未配置 Key） */
  used_fallback?: boolean
}

export interface ChatMessage {
  id: number
  role: 'user' | 'agent'
  content: string
  created_at: string
  book_id?: number | null
}

export interface ChatSession {
  id: number
  name: string
  book_id?: number | null
  created_at: string
  updated_at: string
}

export interface CreateSessionRequest {
  name: string
  book_id?: number | null
}

export interface UpdateSessionRequest {
  name: string
}

export const agentAPI = {
  // 会话管理
  createSession: async (data: CreateSessionRequest) => {
    const response = await apiClient.post<ChatSession>('/api/agent/sessions', data)
    return response.data
  },

  getSessions: async (bookId?: number) => {
    const params = bookId ? { book_id: bookId } : {}
    const response = await apiClient.get<ChatSession[]>('/api/agent/sessions', { params })
    return response.data
  },

  updateSession: async (sessionId: number, data: UpdateSessionRequest) => {
    const response = await apiClient.put<ChatSession>(`/api/agent/sessions/${sessionId}`, data)
    return response.data
  },

  deleteSession: async (sessionId: number) => {
    const response = await apiClient.delete(`/api/agent/sessions/${sessionId}`)
    return response.data
  },

  // 消息管理（对话可能需调用大模型，超时设为 60 秒）
  chat: async (data: ChatMessageRequest) => {
    const response = await apiClient.post<ChatResponse>('/api/agent/chat', data, { timeout: 60000 })
    return response.data
  },

  getMessages: async (sessionId: number, limit = 50) => {
    const response = await apiClient.get<ChatMessage[]>(`/api/agent/sessions/${sessionId}/messages`, {
      params: { limit },
      timeout: 60000,
    })
    return response.data
  },

  deleteMessage: async (messageId: number) => {
    const response = await apiClient.delete(`/api/agent/messages/${messageId}`)
    return response.data
  },

  clearMessages: async (sessionId: number) => {
    const response = await apiClient.delete(`/api/agent/sessions/${sessionId}/messages`)
    return response.data
  },

  /** 生成会话摘要（关闭弹窗时调用，用于跨 session 记忆） */
  summarizeSession: async (sessionId: number) => {
    const response = await apiClient.post<{ summary: string; key_topics: string[]; message_count: number }>(
      `/api/agent/sessions/${sessionId}/summarize`
    )
    return response.data
  },
}
