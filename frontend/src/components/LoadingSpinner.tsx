import { useState, useEffect } from 'react'
import { Loader2 } from 'lucide-react'
import { getRandomTip } from '../utils/emotionTips'

interface LoadingSpinnerProps {
  message?: string
  fullScreen?: boolean
  showEmotionTip?: boolean
}

export default function LoadingSpinner({ 
  message = '加载中...', 
  fullScreen = false,
  showEmotionTip = true 
}: LoadingSpinnerProps) {
  const [currentTip, setCurrentTip] = useState<string>(showEmotionTip ? getRandomTip() : '')

  // 每3秒更换一次tip
  useEffect(() => {
    if (!showEmotionTip) return
    
    const interval = setInterval(() => {
      setCurrentTip(getRandomTip())
    }, 3000)

    return () => clearInterval(interval)
  }, [showEmotionTip])

  const content = (
    <div className="flex flex-col items-center justify-center space-y-4">
      <div className="relative">
        <Loader2 className="w-12 h-12 text-purple-500 animate-spin" />
        <div className="absolute inset-0 border-4 border-purple-200 rounded-full animate-ping opacity-75"></div>
      </div>
      <p className="text-foreground/70 text-sm font-medium">{message}</p>
      {showEmotionTip && currentTip && (
        <div className="mt-4 px-6 py-3 bg-gradient-to-r from-purple-100 to-pink-100 dark:from-purple-900/30 dark:to-pink-900/30 rounded-lg border border-purple-200 dark:border-purple-800">
          <p className="text-foreground/80 text-sm text-center animate-fade-in">
            {currentTip}
          </p>
        </div>
      )}
      <div className="flex space-x-1">
        <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
        <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
        <div className="w-2 h-2 bg-purple-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
      </div>
    </div>
  )

  if (fullScreen) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm">
        {content}
      </div>
    )
  }

  return (
    <div className="py-12">
      {content}
    </div>
  )
}
