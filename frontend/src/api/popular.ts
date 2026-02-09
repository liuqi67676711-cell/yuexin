import { apiClient } from './client'
import { Book } from './books'

export interface BookWithReason extends Book {
  reason?: string  // 推荐理由
}

export const popularAPI = {
  getEveryoneWatching: async (
    skip = 0,
    limit = 20,
    options?: { refresh?: boolean }
  ): Promise<BookWithReason[]> => {
    const params: Record<string, string | number | boolean> = { skip, limit }
    if (options?.refresh) {
      params.refresh = true
      params._t = Date.now() // 避免 HTTP 缓存
    }
    const response = await apiClient.get<BookWithReason[]>('/api/popular/everyone-watching', {
      params,
    })
    return response.data
  },
}
