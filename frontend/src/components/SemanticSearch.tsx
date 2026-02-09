import { useState } from 'react'
import { Sparkles, Search as SearchIcon } from 'lucide-react'
import { recommendationAPI, RecommendationItem } from '../api/recommendation'

interface SemanticSearchProps {
  onRecommendations: (recommendations: RecommendationItem[], message: string) => void
  isLoading: boolean
  setIsLoading: (loading: boolean) => void
}

const INSPIRATION_CAPSULES = [
  { emoji: '☕️', text: '周末独处，想找本温暖治愈的书' },
  { emoji: '💔', text: '最近心情低落，需要一些治愈' },
  { emoji: '🚀', text: '想看点脑洞大开的科幻小说' },
  { emoji: '🌙', text: '深夜了，读点轻松的吧' },
  { emoji: '📚', text: '想深入了解某个历史时期' },
  { emoji: '💡', text: '工作压力大，想放松一下' },
]

export default function SemanticSearch({ onRecommendations, isLoading, setIsLoading }: SemanticSearchProps) {
  const [query, setQuery] = useState('')
  const [error, setError] = useState('')

  const handleSearch = async () => {
    if (!query.trim()) {
      setError('请输入你的心情或需求')
      return
    }

    setIsLoading(true)
    setError('')

    try {
      const response = await recommendationAPI.semanticRecommendation(query)
      onRecommendations(response.recommendations, response.message)
    } catch (err: any) {
      setError(err.response?.data?.detail || '搜索失败，请稍后重试')
    } finally {
      setIsLoading(false)
    }
  }

  const handleCapsuleClick = async (text: string) => {
    // 直接触发推荐，不填入输入框
    setQuery(text)
    setIsLoading(true)
    setError('')

    try {
      const response = await recommendationAPI.semanticRecommendation(text)
      onRecommendations(response.recommendations, response.message)
    } catch (err: any) {
      setError(err.response?.data?.detail || '搜索失败，请稍后重试')
    } finally {
      setIsLoading(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSearch()
    }
  }

  return (
    <div className="w-full max-w-3xl mx-auto">
      <div className="relative">
        <div className="flex items-center space-x-2 mb-4">
          <Sparkles className="w-5 h-5 text-foreground/60" />
          <h2 className="text-lg font-medium text-foreground">告诉我你的心情或需求</h2>
        </div>

        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="例如：最近工作压力大，想看点脑洞大开的科幻小说..."
          className="w-full px-4 py-3 rounded-lg bg-card border border-border text-foreground placeholder-foreground/40 focus:outline-none focus:ring-2 focus:ring-foreground/20 resize-none"
          rows={3}
        />

        {error && (
          <p className="mt-2 text-sm text-red-500">{error}</p>
        )}

        <button
          onClick={handleSearch}
          disabled={isLoading}
          className="mt-4 w-full px-6 py-3 bg-foreground text-background rounded-lg hover:opacity-90 transition-opacity disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
        >
          <SearchIcon className="w-5 h-5" />
          <span>{isLoading ? '正在思考...' : '开始推荐'}</span>
        </button>
      </div>

      {/* 灵感胶囊 */}
      <div className="mt-6">
        <p className="text-sm text-foreground/60 mb-3">灵感胶囊：</p>
        <div className="flex flex-wrap gap-2">
          {INSPIRATION_CAPSULES.map((capsule, index) => (
            <button
              key={index}
              onClick={() => handleCapsuleClick(capsule.text)}
              className="px-4 py-2 rounded-full bg-card border border-border hover:bg-background transition-colors text-sm"
            >
              <span className="mr-1">{capsule.emoji}</span>
              {capsule.text}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
