import { useState } from 'react'

interface OptimizedImageProps {
  src: string | null | undefined
  alt: string
  className?: string
  placeholder?: React.ReactNode
  onError?: () => void
}

export default function OptimizedImage({
  src,
  alt,
  className = '',
  placeholder,
  onError,
}: OptimizedImageProps) {
  const [isLoading, setIsLoading] = useState(true)
  const [hasError, setHasError] = useState(false)

  if (!src || hasError) {
    return (
      <div className={`flex items-center justify-center bg-background border border-border ${className}`}>
        {placeholder || (
          <div className="text-center p-2">
            <div className="text-xs text-foreground/30">暂无封面</div>
          </div>
        )}
      </div>
    )
  }

  return (
    <div className="relative w-full h-full">
      {isLoading && (
        <div className="absolute inset-0 flex items-center justify-center bg-background border border-border">
          <div className="w-6 h-6 border-2 border-foreground/20 border-t-foreground/60 rounded-full animate-spin" />
        </div>
      )}
      <img
        src={src}
        alt={alt}
        className={`w-full h-full object-cover ${isLoading ? 'opacity-0' : 'opacity-100'} transition-opacity duration-200 ${className}`}
        loading="lazy"
        decoding="async"
        onLoad={() => setIsLoading(false)}
        onError={() => {
          setIsLoading(false)
          setHasError(true)
          onError?.()
        }}
      />
    </div>
  )
}
