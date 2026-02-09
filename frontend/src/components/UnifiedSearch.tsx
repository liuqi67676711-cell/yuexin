import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Search as SearchIcon, Sparkles, BookOpen } from 'lucide-react'
import { RecommendationItem } from '../api/recommendation'

type SearchMode = 'semantic' | 'exact'

const SEARCH_MODE_STORAGE_KEY = 'yuexin_search_mode'

interface UnifiedSearchProps {
  onRecommendations?: (recommendations: RecommendationItem[], message: string) => void
  onSearchResults?: (books: any[]) => void
  setIsLoading?: (loading: boolean) => void
}

export default function UnifiedSearch({ 
  onRecommendations: _onRecommendations, 
  onSearchResults: _onSearchResults,
  setIsLoading: _setIsLoading 
}: UnifiedSearchProps) {
  const navigate = useNavigate()
  const [query, setQuery] = useState('')
  const [isSearching, _setIsSearching] = useState(false)
  
  // 从 localStorage 读取保存的搜索模式，如果没有则使用默认值
  const [searchMode, setSearchMode] = useState<SearchMode>(() => {
    if (typeof window !== 'undefined') {
      const savedMode = localStorage.getItem(SEARCH_MODE_STORAGE_KEY)
      if (savedMode === 'semantic' || savedMode === 'exact') {
        return savedMode as SearchMode
      }
    }
    return 'semantic' // 默认值
  })

  // 当搜索模式改变时，保存到 localStorage
  const handleModeChange = (mode: SearchMode) => {
    setSearchMode(mode)
    if (typeof window !== 'undefined') {
      localStorage.setItem(SEARCH_MODE_STORAGE_KEY, mode)
    }
  }

  const handleSearch = () => {
    if (!query.trim()) {
      alert('请输入搜索内容')
      return
    }

    console.log('开始搜索:', query, '模式:', searchMode)
    
    if (searchMode === 'semantic') {
      // 语义推荐 - 跳转到推荐结果页面
      navigate(`/recommendations?q=${encodeURIComponent(query)}`)
    } else {
      // 精确搜索 - 跳转到搜索页面
      navigate(`/search?q=${encodeURIComponent(query)}`)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSearch()
    }
  }

  return (
    <div className="relative w-full max-w-3xl mx-auto">
      {/* 模式切换 Tab */}
      <div className="flex items-center justify-center mb-4 gap-2 h-10">
        <button
          onClick={() => handleModeChange('semantic')}
          className={`flex items-center justify-center gap-2 px-4 py-2 rounded-lg transition-all duration-200 min-w-[120px] ${
            searchMode === 'semantic'
              ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-lg'
              : 'bg-background border border-border text-foreground/70 hover:bg-background/80'
          }`}
        >
          <Sparkles className="w-4 h-4 flex-shrink-0" />
          <span className="text-sm font-medium whitespace-nowrap">语义搜索</span>
        </button>
        <button
          onClick={() => handleModeChange('exact')}
          className={`flex items-center justify-center gap-2 px-4 py-2 rounded-lg transition-all duration-200 min-w-[120px] ${
            searchMode === 'exact'
              ? 'bg-gradient-to-r from-purple-500 to-pink-500 text-white shadow-lg'
              : 'bg-background border border-border text-foreground/70 hover:bg-background/80'
          }`}
        >
          <BookOpen className="w-4 h-4 flex-shrink-0" />
          <span className="text-sm font-medium whitespace-nowrap">精确搜索</span>
        </button>
      </div>

      {/* 搜索框 */}
      <div className="relative flex items-center w-full">
        {searchMode === 'semantic' ? (
          <Sparkles className="absolute left-4 w-5 h-5 text-purple-500 z-10 flex-shrink-0" />
        ) : (
          <BookOpen className="absolute left-4 w-5 h-5 text-purple-500 z-10 flex-shrink-0" />
        )}
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={
            searchMode === 'semantic'
              ? '告诉我你的心情或需求，例如：最近工作压力大，想看点轻松的书...'
              : '搜索书名、作者或ISBN，例如：白鹿原、陈忠实、9787101003048...'
          }
          disabled={isSearching}
          className="w-full pl-12 pr-14 py-4 rounded-full bg-white/90 dark:bg-white/90 backdrop-blur-sm border border-border/50 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50 transition-colors text-base text-black disabled:opacity-50 disabled:cursor-not-allowed"
          style={{ 
            minHeight: '56px',
            height: '56px',
            boxSizing: 'border-box'
          }}
        />
        <button
          onClick={handleSearch}
          disabled={isSearching}
          className="absolute right-2 p-2.5 rounded-full bg-gradient-to-r from-purple-500 to-pink-500 text-white hover:opacity-90 transition-opacity disabled:opacity-50 shadow-lg disabled:cursor-not-allowed"
        >
          {isSearching ? (
            <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
          ) : (
            <SearchIcon className="w-5 h-5" />
          )}
        </button>
      </div>
      {isSearching && (
        <div className="mt-4 text-center text-sm text-foreground/60">
          <p>正在搜索，这可能需要10-15秒...</p>
        </div>
      )}
    </div>
  )
}
