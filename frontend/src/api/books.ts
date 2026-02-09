import { apiClient } from './client'

export interface Book {
  id: number
  isbn?: string
  title: string
  author?: string
  publisher?: string
  description?: string
  cover_url?: string
  rating?: number
  category?: string
  page_count?: number
  reason?: string  // 推荐理由（用于搜索结果和热门书籍）
}

export interface GenerateDescriptionResponse {
  description: string
  used_fallback: boolean
}

export interface GenerateCoverResponse {
  cover_url: string
  used_fallback: boolean
  message: string
}

export const booksAPI = {
  getBook: async (id: number) => {
    const response = await apiClient.get<Book>(`/api/books/${id}`)
    return response.data
  },

  listBooks: async (skip = 0, limit = 20) => {
    const response = await apiClient.get<Book[]>('/api/books', {
      params: { skip, limit },
    })
    return response.data
  },

  generateDescription: async (bookId: number) => {
    const response = await apiClient.post<GenerateDescriptionResponse>(
      `/api/books/${bookId}/generate-description`
    )
    return response.data
  },

  generateCover: async (bookId: number) => {
    const response = await apiClient.post<GenerateCoverResponse>(
      `/api/books/${bookId}/generate-cover`
    )
    return response.data
  },
}
