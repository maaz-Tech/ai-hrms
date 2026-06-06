import { createContext, useContext, useEffect, useState } from 'react'
import api from '../api/client'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem('user')
    return raw ? JSON.parse(raw) : null
  })
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    // Validate token on load if present
    if (localStorage.getItem('token') && !user) {
      api.get('/api/auth/me').then((r) => persist(r.data)).catch(() => logout())
    }
  }, []) // eslint-disable-line

  function persist(u) {
    setUser(u)
    localStorage.setItem('user', JSON.stringify(u))
  }

  async function login(email, password) {
    setLoading(true)
    try {
      const body = new URLSearchParams({ username: email, password })
      const { data } = await api.post('/api/auth/login', body)
      localStorage.setItem('token', data.access_token)
      persist({ email: data.email, full_name: data.full_name, role: data.role })
      return data
    } finally {
      setLoading(false)
    }
  }

  function logout() {
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, login, logout, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)

export const ROLE_LABELS = {
  management_admin: 'Management Admin',
  senior_manager: 'Senior Manager',
  hr_recruiter: 'HR Recruiter',
  employee: 'Employee',
}
