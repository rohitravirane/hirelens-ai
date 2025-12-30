'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import api from '@/lib/api'

export function useAuth() {
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isLoading, setIsLoading] = useState(true)
  const [user, setUser] = useState<any>(null)
  const router = useRouter()

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
    // Clear all auth data immediately
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    
    // Clear state
    setIsAuthenticated(false)
    setUser(null)
    
    // Clear any cached queries/data
    if (typeof window !== 'undefined') {
      // Clear all localStorage items related to auth
      Object.keys(localStorage).forEach(key => {
        if (key.startsWith('auth_') || key.startsWith('user_') || key.startsWith('token_')) {
          localStorage.removeItem(key)
        }
      })
    }
    
    // Immediately redirect to login page - use window.location for immediate redirect
    if (typeof window !== 'undefined') {
      window.location.href = '/login'
    } else {
      router.push('/login')
    }
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

