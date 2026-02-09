import { useState, useRef, useEffect } from 'react'
import { Bot } from 'lucide-react'
import AgentChatModal from './AgentChatModal'

export default function FloatingAgentButton() {
  const [isDragging, setIsDragging] = useState(false)
  const [hasDragged, setHasDragged] = useState(false) // 标记是否发生了拖拽
  const [position, setPosition] = useState({ x: window.innerWidth - 100, y: window.innerHeight - 100 })
  const [isModalOpen, setIsModalOpen] = useState(false)
  const dragStartPos = useRef({ x: 0, y: 0 }) // 鼠标相对于按钮的偏移
  const mouseStartPos = useRef({ x: 0, y: 0 }) // 鼠标的初始绝对位置
  const buttonRef = useRef<HTMLButtonElement>(null)
  
  // 响应式：监听窗口大小变化，确保按钮始终可见
  useEffect(() => {
    const handleResize = () => {
      const maxX = window.innerWidth - 60
      const maxY = window.innerHeight - 60
      setPosition((prev) => ({
        x: Math.min(prev.x, maxX),
        y: Math.min(prev.y, maxY)
      }))
    }
    
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  useEffect(() => {
    // 从localStorage恢复位置，并确保在视窗内
    const savedPos = localStorage.getItem('agentButtonPosition')
    if (savedPos) {
      try {
        const pos = JSON.parse(savedPos)
        // 确保位置在视窗内
        const maxX = window.innerWidth - 60
        const maxY = window.innerHeight - 60
        setPosition({
          x: Math.min(pos.x, maxX),
          y: Math.min(pos.y, maxY)
        })
      } catch (e) {
        // 忽略解析错误，使用默认位置
        setPosition({ x: window.innerWidth - 100, y: window.innerHeight - 100 })
      }
    } else {
      // 默认位置：右下角，但确保在小屏幕上也能看到
      const defaultX = Math.max(20, window.innerWidth - 100)
      const defaultY = Math.max(20, window.innerHeight - 100)
      setPosition({ x: defaultX, y: defaultY })
    }
  }, [])

  const handleMouseDown = (e: React.MouseEvent) => {
    if (buttonRef.current) {
      const rect = buttonRef.current.getBoundingClientRect()
      dragStartPos.current = {
        x: e.clientX - rect.left,
        y: e.clientY - rect.top
      }
      mouseStartPos.current = {
        x: e.clientX,
        y: e.clientY
      }
      setIsDragging(true)
      setHasDragged(false) // 重置拖拽标记
    }
  }

  const handleMouseMove = (e: MouseEvent) => {
    if (isDragging) {
      const newX = e.clientX - dragStartPos.current.x
      const newY = e.clientY - dragStartPos.current.y
      
      // 计算相对于鼠标按下时的移动距离
      const deltaX = Math.abs(e.clientX - mouseStartPos.current.x)
      const deltaY = Math.abs(e.clientY - mouseStartPos.current.y)
      
      // 如果移动距离超过5px，认为是拖拽
      if (deltaX > 5 || deltaY > 5) {
        setHasDragged(true)
      }
      
      // 限制在视窗内
      const maxX = window.innerWidth - 60
      const maxY = window.innerHeight - 60
      const minX = 0
      const minY = 0
      
      setPosition({
        x: Math.max(minX, Math.min(maxX, newX)),
        y: Math.max(minY, Math.min(maxY, newY))
      })
    }
  }

  const handleMouseUp = () => {
    if (isDragging) {
      setIsDragging(false)
      // 保存位置到localStorage
      localStorage.setItem('agentButtonPosition', JSON.stringify(position))
      // 延迟重置hasDragged，避免立即触发点击事件
      setTimeout(() => {
        setHasDragged(false)
      }, 100)
    }
  }

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
      return () => {
        document.removeEventListener('mousemove', handleMouseMove)
        document.removeEventListener('mouseup', handleMouseUp)
      }
    }
  }, [isDragging, position])

  const handleClick = (_e: React.MouseEvent) => {
    // 如果发生了拖拽，不打开模态窗
    if (hasDragged || isDragging) {
      return
    }
    setIsModalOpen(true)
  }

  return (
    <>
      <button
        ref={buttonRef}
        onClick={handleClick}
        onMouseDown={handleMouseDown}
        className="fixed z-50 w-14 h-14 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 shadow-lg hover:shadow-xl transition-all duration-200 flex items-center justify-center text-white cursor-move hover:scale-110 active:scale-95"
        style={{
          left: `${position.x}px`,
          top: `${position.y}px`,
          cursor: isDragging ? 'grabbing' : 'grab'
        }}
        title="AI 书童 - 拖拽移动"
      >
        <Bot className="w-6 h-6" />
      </button>

      <AgentChatModal
        bookId={null}
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </>
  )
}
