import { apiClient } from './client'

export interface RegisterData {
  email: string
  username: string
  password: string
}

export interface LoginData {
  email: string
  password: string
}

export interface User {
  id: number
  email: string
  username: string
  agent_name: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user_id: number
  username: string
}

export const authAPI = {
  register: async (data: RegisterData) => {
    const response = await apiClient.post<User>('/api/auth/register', data)
    return response.data
  },

  login: async (data: LoginData) => {
    const formData = new FormData()
    formData.append('username', data.email)
    formData.append('password', data.password)
    
    const response = await apiClient.post<TokenResponse>('/api/auth/login', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    
    if (response.data.access_token) {
      localStorage.setItem('token', response.data.access_token)
    }
    
    return response.data
  },

  getCurrentUser: async () => {
    const response = await apiClient.get<User>('/api/auth/me')
    return response.data
  },

  updateAgentName: async (agentName: string) => {
    const response = await apiClient.put<User>('/api/auth/agent-name', {
      agent_name: agentName,
    })
    return response.data
  },

  guestLogin: async (browserId: string) => {
    const response = await apiClient.post<{
      user: User
      access_token: string
      token_type: string
    }>('/api/auth/guest-login', {
      browser_id: browserId,
    })
    return response.data
  },
}
