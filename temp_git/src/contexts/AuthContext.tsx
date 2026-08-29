import { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react'
import { User } from '../types'
import { supabase, signIn as supabaseSignIn, signOut as supabaseSignOut, getSession, getUser, onAuthStateChange } from '../services/supabase'

interface AuthContextType {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
  login: (email: string, password: string, rememberMe?: boolean) => Promise<void>
  logout: () => Promise<void>
  refreshToken: () => Promise<void>
  updateProfile: (data: Partial<User>) => Promise<void>
  changePassword: (currentPassword: string, newPassword: string) => Promise<void>
  requestPasswordReset: (email: string) => Promise<void>
  resetPassword: (token: string, newPassword: string) => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

const DEMO_USER: User = {
  id: '1',
  email: 'demo@medfusion.ai',
  name: 'Dr. Sarah Chen',
  role: 'physician',
  avatar: undefined,
  preferences: {
    theme: 'system',
    language: 'en',
    timezone: 'America/Los_Angeles',
    notifications: {
      email: true,
      push: true,
      criticalAlerts: true,
    },
    dashboard: {
      defaultView: 'overview',
      widgets: ['vitals', 'labs', 'imaging', 'ai-insights', 'risk-scores'],
    },
    imaging: {
      defaultWindowLevel: { width: 400, center: 40 },
      cineSpeed: 15,
      showAnnotations: true,
    },
  },
  createdAt: '2024-01-15T08:00:00Z',
  lastLoginAt: new Date().toISOString(),
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [useSupabase, setUseSupabase] = useState(false)

  useEffect(() => {
    const initAuth = async () => {
      // Check if Supabase is configured
      setUseSupabase(!!supabase)

      if (supabase) {
        // Try Supabase session first
        const { data: { session } } = await getSession()
        if (session?.user) {
          const { data: { user: sbUser } } = await getUser()
          if (sbUser) {
            const mappedUser: User = {
              id: sbUser.id,
              email: sbUser.email || '',
              name: sbUser.user_metadata?.full_name || sbUser.email?.split('@')[0] || 'User',
              role: sbUser.user_metadata?.role || 'physician',
              avatar: sbUser.user_metadata?.avatar_url,
              preferences: {
                theme: 'system',
                language: 'en',
                timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                notifications: {
                  email: true,
                  push: true,
                  criticalAlerts: true,
                },
                dashboard: {
                  defaultView: 'overview',
                  widgets: ['vitals', 'labs', 'imaging', 'ai-insights', 'risk-scores'],
                },
                imaging: {
                  defaultWindowLevel: { width: 400, center: 40 },
                  cineSpeed: 15,
                  showAnnotations: true,
                },
              },
              createdAt: sbUser.created_at,
              lastLoginAt: new Date().toISOString(),
            }
            setUser(mappedUser)
            setIsLoading(false)
            return
          }
        }
      }

      // Fallback to demo/localStorage
      const token = localStorage.getItem('auth_token')
      const storedUser = localStorage.getItem('user')

      if (token && storedUser) {
        try {
          setUser(JSON.parse(storedUser))
        } catch {
          localStorage.removeItem('auth_token')
          localStorage.removeItem('refresh_token')
          localStorage.removeItem('user')
        }
      }
      setIsLoading(false)
    }

    initAuth()

    // Listen for auth changes if using Supabase
    if (supabase) {
      const { data: { subscription } } = onAuthStateChange(async (event, session) => {
        if (event === 'SIGNED_IN' && session?.user) {
          const { data: { user: sbUser } } = await getUser()
          if (sbUser) {
            const mappedUser: User = {
              id: sbUser.id,
              email: sbUser.email || '',
              name: sbUser.user_metadata?.full_name || sbUser.email?.split('@')[0] || 'User',
              role: sbUser.user_metadata?.role || 'physician',
              avatar: sbUser.user_metadata?.avatar_url,
              preferences: {
                theme: 'system',
                language: 'en',
                timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
                notifications: {
                  email: true,
                  push: true,
                  criticalAlerts: true,
                },
                dashboard: {
                  defaultView: 'overview',
                  widgets: ['vitals', 'labs', 'imaging', 'ai-insights', 'risk-scores'],
                },
                imaging: {
                  defaultWindowLevel: { width: 400, center: 40 },
                  cineSpeed: 15,
                  showAnnotations: true,
                },
              },
              createdAt: sbUser.created_at,
              lastLoginAt: new Date().toISOString(),
            }
            setUser(mappedUser)
          }
        } else if (event === 'SIGNED_OUT') {
          setUser(null)
        }
      })

      return () => subscription.unsubscribe()
    }
  }, [])

  const login = useCallback(async (email: string, password: string, rememberMe = false) => {
    setIsLoading(true)

    try {
      if (useSupabase && supabase) {
        const { error } = await supabaseSignIn(email, password)
        if (error) throw error
        // Session will be set via onAuthStateChange
        setIsLoading(false)
        return
      }

      // Demo fallback
      await new Promise(resolve => setTimeout(resolve, 1000))

      if (email === 'demo@medfusion.ai' && password === 'demo123') {
        const token = 'demo-jwt-token-' + Date.now()
        const refresh = 'demo-refresh-token-' + Date.now()

        localStorage.setItem('auth_token', token)
        localStorage.setItem('refresh_token', refresh)
        localStorage.setItem('user', JSON.stringify(DEMO_USER))

        if (rememberMe) {
          localStorage.setItem('remember_me', 'true')
        }

        setUser(DEMO_USER)
        setIsLoading(false)
        return
      }

      throw new Error('Invalid credentials. Use demo@medfusion.ai / demo123')
    } catch (err) {
      setIsLoading(false)
      throw err
    }
  }, [useSupabase])

  const logout = useCallback(async () => {
    if (useSupabase && supabase) {
      await supabaseSignOut()
      setUser(null)
      return
    }

    localStorage.removeItem('auth_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    localStorage.removeItem('remember_me')
    setUser(null)
  }, [useSupabase])

  const refreshToken = useCallback(async () => {
    const refresh = localStorage.getItem('refresh_token')
    if (!refresh) throw new Error('No refresh token')

    await new Promise(resolve => setTimeout(resolve, 500))
    const newToken = 'demo-jwt-token-' + Date.now()
    localStorage.setItem('auth_token', newToken)
  }, [])

  const updateProfile = useCallback(async (data: Partial<User>) => {
    if (!user) throw new Error('Not authenticated')
    const updated = { ...user, ...data }
    localStorage.setItem('user', JSON.stringify(updated))
    setUser(updated)
  }, [user])

  const changePassword = useCallback(async (_currentPassword: string, _newPassword: string) => {
    await new Promise(resolve => setTimeout(resolve, 1000))
  }, [])

  const requestPasswordReset = useCallback(async (_email: string) => {
    await new Promise(resolve => setTimeout(resolve, 1000))
  }, [])

  const resetPassword = useCallback(async (_token: string, _newPassword: string) => {
    await new Promise(resolve => setTimeout(resolve, 1000))
  }, [])

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated: !!user,
        isLoading,
        login,
        logout,
        refreshToken,
        updateProfile,
        changePassword,
        requestPasswordReset,
        resetPassword,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}