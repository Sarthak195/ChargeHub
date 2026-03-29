import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { authApi } from '../api/client'

interface User {
  id: number
  email: string
  full_name: string
  unit_number: string | null
  role: 'resident' | 'admin'
}

interface AuthCtx {
  user: User | null
  token: string | null
  login: (email: string, password: string) => Promise<void>
  register: (data: any) => Promise<void>
  logout: () => void
  isAdmin: boolean
  loading: boolean
}

const AuthContext = createContext<AuthCtx | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'))
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (token) {
      authApi.me()
        .then((r) => setUser(r.data))
        .catch(() => { localStorage.removeItem('token'); setToken(null) })
        .finally(() => setLoading(false))
    } else {
      setLoading(false)
    }
  }, [token])

  const login = async (email: string, password: string) => {
    const r = await authApi.login(email, password)
    const { access_token, user: u } = r.data
    localStorage.setItem('token', access_token)
    setToken(access_token)
    setUser(u)
  }

  const register = async (data: any) => {
    const r = await authApi.register(data)
    const { access_token, user: u } = r.data
    localStorage.setItem('token', access_token)
    setToken(access_token)
    setUser(u)
  }

  const logout = () => {
    localStorage.removeItem('token')
    setToken(null)
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, token, login, register, logout, isAdmin: user?.role === 'admin', loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
