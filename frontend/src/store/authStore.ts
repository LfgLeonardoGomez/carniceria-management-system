import { create } from 'zustand'

interface User {
  id: string
  email: string
  nombre: string
  apellido: string
  rol: string
  empresa_id?: string | null
  original_role?: string | null
}

interface AuthState {
  user: User | null
  token: string | null
  isAuthenticated: boolean
  isImpersonating: boolean
  setUser: (user: User) => void
  setToken: (token: string) => void
  setImpersonating: (impersonating: boolean) => void
  logout: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  token: null,
  isAuthenticated: false,
  isImpersonating: false,
  setUser: (user) => {
    const isImpersonating = user.original_role === 'superadmin' && user.rol === 'admin'
    set({ user, isAuthenticated: true, isImpersonating })
  },
  setToken: (token) => set({ token }),
  setImpersonating: (isImpersonating) => set({ isImpersonating }),
  logout: () => set({ user: null, token: null, isAuthenticated: false, isImpersonating: false }),
}))
