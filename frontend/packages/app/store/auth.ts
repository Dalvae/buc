import { create } from 'zustand'
import { persist, createJSONStorage } from 'zustand/middleware'
import type { UserPublic } from 'app/api/hooks/users'

interface AuthState {
  token: string | null
  user: UserPublic | null
  status: 'idle' | 'loading' | 'authenticated' | 'unauthenticated'
  theme: 'light' | 'dark'
  demoCompanyId: string | null // Nuevo campo
  setToken: (token: string) => void
  setUser: (user: UserPublic) => void
  setTheme: (theme: 'light' | 'dark') => void
  setDemoCompanyId: (id: string) => void // Nueva acción
  logout: () => void
}

export const useAuthStore = create(
  persist<AuthState>(
    (set) => ({
      token: null,
      user: null,
      status: 'idle',
      theme: 'light',
      demoCompanyId: null, // Valor inicial
      setToken: (token) => {
        set({ token, status: 'authenticated' })
      },
      setUser: (user) => set({ user }),
      setTheme: (theme) => set({ theme }),
      setDemoCompanyId: (id) => set({ demoCompanyId: id }), // Implementación de la acción
      logout: () => {
        set({ token: null, user: null, status: 'unauthenticated' })
      },
    }),
    {
      name: 'auth-storage', // unique name
      storage: createJSONStorage(() => localStorage), // (optional) by default, 'localStorage' is used
    }
  )
)
