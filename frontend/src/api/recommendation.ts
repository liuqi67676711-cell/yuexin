import { apiClient } from './client'

export interface RecommendationItem {
  book_id: number
  title: string
  author: string
  cover_url: string
  rating: number
  recommendation_text: string
  highlighted_words: string[]
}

export interface RecommendationResponse {
  recommendations: RecommendationItem[]
  message: string
  show_agent_suggestion?: boolean  // 是否显示AI书童引导
  agent_name?: string  // AI书童名称
}

export const recommendationAPI = {
  semanticRecommendation: async (query: string, signal?: AbortSignal) => {
    const response = await apiClient.post<RecommendationResponse>(
      '/api/recommendation/semantic',
      { query },
      { timeout: 90000, signal }
    )
    return response.data
  },
}
