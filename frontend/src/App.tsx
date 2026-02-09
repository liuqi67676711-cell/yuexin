import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import HomePage from './pages/HomePage'
import BookshelfPage from './pages/BookshelfPage'
import RecommendationResultsPage from './pages/RecommendationResultsPage'
import SearchResultsPage from './pages/SearchResultsPage'
import { ErrorBoundary } from './components/ErrorBoundary'
import FloatingAgentButton from './components/FloatingAgentButton'
import ToastContainer from './components/ToastContainer'

function App() {
  return (
    <ErrorBoundary>
      <Router>
        {/* Toast通知容器 */}
        <ToastContainer />
        {/* AI书童悬浮按钮 - 全局显示 */}
        <FloatingAgentButton />
        <Routes>
        <Route
          path="/"
          element={
            <Layout>
              <HomePage />
            </Layout>
          }
        />
        <Route
          path="/recommendations"
          element={
            <Layout>
              <RecommendationResultsPage />
            </Layout>
          }
        />
        <Route
          path="/search"
          element={
            <Layout>
              <SearchResultsPage />
            </Layout>
          }
        />
        <Route
          path="/bookshelf"
          element={
            <Layout>
              <BookshelfPage />
            </Layout>
          }
        />
        {/* 404 重定向到首页 */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
      </Router>
    </ErrorBoundary>
  )
}

export default App
