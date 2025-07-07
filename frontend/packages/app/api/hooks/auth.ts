import { useMutation, useQuery } from '@tanstack/react-query'
import createClient from 'openapi-fetch'
import type { components } from 'app/client'
import { useAuthStore } from 'app/store/auth'

const { POST, GET } = createClient({ baseUrl: '/api/v1' })

export type User = components['schemas']['UserPublic']
export type LoginRequest = components['schemas']['Body_login_login_access_token']

export function useLogin() {
  const { setToken } = useAuthStore()

  return useMutation({
    mutationFn: async (data: LoginRequest) => {
      const { data: tokenData, error } = await POST('/login/access-token', {
        body: data,
      })

      if (error) {
        throw new Error('Failed to login')
      }
      return tokenData
    },
    onSuccess: (data) => {
      if (data?.access_token) {
        setToken(data.access_token)
      }
    },
  })
}

export function useUser() {
  const { token, setUser } = useAuthStore()

  return useQuery<User, Error>({
    queryKey: ['user'],
    queryFn: async () => {
      const { data, error } = await GET('/users/me')
      if (error) {
        throw new Error('Failed to fetch user')
      }
      return data
    },
    enabled: !!token,
    onSuccess: (data) => {
      setUser(data)
    },
  })
}

export type RegisterRequest = components['schemas']['UserRegister']
export type UpdateMeRequest = components['schemas']['UserUpdateMe']

export function useRegister() {
  return useMutation({
    mutationFn: async (data: RegisterRequest) => {
      const { data: user, error } = await POST('/users/signup', {
        body: data,
      })

      if (error) {
        throw new Error('Failed to register')
      }
      return user
    },
  })
}

import { useAppToast } from 'app/hooks/useAppToast'

export function useUpdateMe() {
  const { setUser } = useAuthStore()
  const showToast = useAppToast()

  return useMutation({
    mutationFn: async (data: UpdateMeRequest) => {
      const { data: user, error } = await PATCH('/users/me', {
        body: data,
      })

      if (error) {
        showToast('Error', { message: 'No se pudo actualizar el perfil.', type: 'error' })
        throw new Error('Failed to update user')
      }
      return user
    },
    onSuccess: (data) => {
      if (data) {
        setUser(data)
        showToast('Éxito', { message: 'Perfil actualizado correctamente.', type: 'success' })
      }
    },
  })
}

export function useDeleteMe() {
  const { logout } = useAuthStore()
  return useMutation({
    mutationFn: async () => {
      const { error } = await DELETE('/users/me')

      if (error) {
        throw new Error('Failed to delete user')
      }
    },
    onSuccess: () => {
      logout()
    },
  })
}
