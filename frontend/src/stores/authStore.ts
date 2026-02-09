import { create } from 'zustand'
import { User, authAPI } from '../api/auth'
import { getBrowserId } from '../utils/browserId'

interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  register: (email: string, username: string, password: string) => Promise<void>
  guestLogin: () => Promise<User | void>
  logout: () => void
  fetchUser: () => Promise<void>
  updateAgentName: (agentName: string) => Promise<void>
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  isAuthenticated: false,
  isLoading: false,

  login: async (email: string, password: string) => {
    set({ isLoading: true })
    try {
      await authAPI.login({ email, password })
      await authAPI.getCurrentUser().then((user) => {
        set({ user, isAuthenticated: true, isLoading: false })
      })
    } catch (error) {
      set({ isLoading: false })
      throw error
    }
  },

  register: async (email: string, username: string, password: string) => {
    set({ isLoading: true })
    try {
      // 先注册
      await authAPI.register({ email, username, password })
      // 注册成功后自动登录
      await authAPI.login({ email, password })
      // 获取用户信息
      const user = await authAPI.getCurrentUser()
      set({ user, isAuthenticated: true, isLoading: false })
    } catch (error: any) {
      set({ isLoading: false })
      console.error('注册失败:', error)
      throw error
    }
  },

  logout: () => {
    localStorage.removeItem('token')
    set({ user: null, isAuthenticated: false })
  },

  guestLogin: async () => {
    set({ isLoading: true })
    try {
      const browserId = getBrowserId()
      console.log('开始访客登录，browserId:', browserId)
      const response = await authAPI.guestLogin(browserId)
      console.log('访客登录响应:', response)
      // 保存token
      if (response.access_token) {
        localStorage.setItem('token', response.access_token)
        console.log('Token已保存')
      }
      // 获取用户信息
      const currentUser = await authAPI.getCurrentUser()
      console.log('获取用户信息成功:', currentUser)
      set({ user: currentUser, isAuthenticated: true, isLoading: false })
      return currentUser
    } catch (error: any) {
      console.error('访客登录失败:', error)
      console.error('错误详情:', error.response?.data || error.message)
      set({ isLoading: false, isAuthenticated: false, user: null })
      throw error  // 重新抛出错误，让调用者处理
    }
  },

  fetchUser: async () => {
    const token = localStorage.getItem('token')
    if (!token) {
      // 如果没有token，尝试访客登录
      try {
        await useAuthStore.getState().guestLogin()
      } catch (error) {
        set({ isAuthenticated: false, user: null })
      }
      return
    }

    set({ isLoading: true })
    try {
      const user = await authAPI.getCurrentUser()
      set({ user, isAuthenticated: true, isLoading: false })
    } catch (error) {
      localStorage.removeItem('token')
      // 如果token失效，尝试访客登录
      try {
        await useAuthStore.getState().guestLogin()
      } catch (error) {
        set({ user: null, isAuthenticated: false, isLoading: false })
      }
    }
  },

  updateAgentName: async (agentName: string) => {
    try {
      const user = await authAPI.updateAgentName(agentName)
      set({ user })
    } catch (error) {
      throw error
    }
  },
}))
