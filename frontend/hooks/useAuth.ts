import { useState, useEffect } from 'react'
import api from '@/lib/api'

export function useAuth() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [user, setUser] = useState<any>(null)

  useEffect(() => {
    checkAuth()
  }, [])

  const checkAuth = async () => {
    try {
      const token = localStorage.getItem('access_token')
      if (!token) {
        setIsAuthenticated(false)
        setIsLoading(false)
        return
      }

      const response = await api.get('/api/v1/auth/me')
      setUser(response.data)
      setIsAuthenticated(true)
    } catch (error) {
      setIsAuthenticated(false)
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
    } finally {
      setIsLoading(false)
    }
  }

  const login = async (email: string, password: string) => {
    const response = await api.post('/api/v1/auth/login', { email, password })
    const { access_token, refresh_token } = response.data
    localStorage.setItem('access_token', access_token)
    localStorage.setItem('refresh_token', refresh_token)
    await checkAuth()
    return response.data
  }

  const logout = () => {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    setIsAuthenticated(false)
    setUser(null)
  }

  return {
    isAuthenticated,
    isLoading,
    user,
    login,
    logout,
    checkAuth,
  }
}

