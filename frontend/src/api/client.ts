import axios from 'axios'

// 使用相对路径，通过 Vite 代理访问后端
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || ''

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30秒超时
})

// 请求拦截器（已移除token逻辑，因为不需要登录）
apiClient.interceptors.request.use(
  (config) => {
    // 不再需要添加token
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器：处理错误
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // 检查是否是网络错误
    if (!error.response) {
      if (error.code === 'ECONNABORTED') {
        console.error('请求超时:', error)
        return Promise.reject(new Error('请求超时，请稍后重试'))
      } else if (error.message === 'Network Error' || error.code === 'ERR_NETWORK') {
        console.error('网络错误:', error)
        return Promise.reject(new Error('网络连接失败，请检查后端服务是否运行（http://localhost:8000）'))
      }
    }
    // 已移除401错误处理，因为不需要登录
    return Promise.reject(error)
  }
)
