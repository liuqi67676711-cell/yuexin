import { apiClient } from './client'
import { Book } from './books'

export type BookshelfStatus = 'to_read' | 'reading' | 'read' | 'dropped'

export interface BookshelfItem {
  id: number
  book: Book
  status: BookshelfStatus
  notes?: string
}

export interface AddToBookshelfRequest {
  book_id: number
  status?: BookshelfStatus
}

export interface UpdateBookshelfRequest {
  status?: BookshelfStatus
  notes?: string
}

export const bookshelfAPI = {
  getBookshelf: async (status?: BookshelfStatus) => {
    const response = await apiClient.get<BookshelfItem[]>('/api/bookshelf', {
      params: status ? { status } : {},
    })
    return response.data
  },

  addToBookshelf: async (data: AddToBookshelfRequest) => {
    const response = await apiClient.post<BookshelfItem>('/api/bookshelf/add', data)
    return response.data
  },

  updateBookshelf: async (id: number, data: UpdateBookshelfRequest) => {
    const response = await apiClient.put<BookshelfItem>(`/api/bookshelf/${id}`, data)
    return response.data
  },

  removeFromBookshelf: async (id: number) => {
    const response = await apiClient.delete(`/api/bookshelf/${id}`)
    return response.data
  },

  markNotInterested: async (book_id: number, reason?: string) => {
    const response = await apiClient.post('/api/bookshelf/not-interested', {
      book_id,
      reason,
    })
    return response.data
  },
}
