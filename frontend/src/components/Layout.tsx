import { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { BookOpen, BookMarked } from 'lucide-react'

interface LayoutProps {
  children: ReactNode
}

export default function Layout({ children }: LayoutProps) {

  return (
    <div className="min-h-screen bg-background">
      {/* 版权声明 */}
      <div className="bg-card border-b border-border py-2 px-4 text-xs text-foreground/60 text-center">
        本平台所有书籍信息来源于公开API，封面图片和简介均来自第三方平台，仅供学习交流使用。
      </div>

      {/* 导航栏 */}
      <nav className="sticky top-0 z-[120] bg-card/80 backdrop-blur-sm border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link to="/" className="flex items-center space-x-2">
              <BookOpen className="w-6 h-6 text-foreground" />
              <span className="text-xl font-semibold text-foreground">Readfor</span>
            </Link>

            <div className="flex items-center space-x-4">
              {/* 心灵驿站入口 */}
              <Link
                to="/bookshelf"
                className="flex items-center space-x-2 px-3 py-2 rounded-lg hover:bg-background transition-colors text-foreground"
                title="心灵驿站"
              >
                <BookMarked className="w-5 h-5" />
                <span className="hidden sm:inline text-sm font-medium">心灵驿站</span>
              </Link>
            </div>
          </div>
        </div>
      </nav>

      {/* 主内容 */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>
  )
}
