import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

// 获取 root 元素
const rootElement = document.getElementById('root')

if (!rootElement) {
  throw new Error('Root element not found')
}

// 创建 React root 并渲染
ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
)
