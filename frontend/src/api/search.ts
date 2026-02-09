import { apiClient } from './client'
import { Book } from './books'

export const searchAPI = {
  exactSearch: async (
    params: { isbn?: string; title?: string; author?: string },
    signal?: AbortSignal
  ) => {
    const response = await apiClient.get<Book[]>('/api/search/exact', { params, signal })
    return response.data
  },
}
