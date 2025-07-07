import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import createClient from 'openapi-fetch'
import type { components } from 'app/client'

const { GET, POST, PATCH } = createClient({ baseUrl: '/api/v1' })

export type User = components['schemas']['UserPublic']
export type BulkMoveRequest = { user_ids: string[]; target_company_id: string }
export type CreateUserRequest = components['schemas']['PrivateUserCreate']
export type UpdateUserRequest = components['schemas']['UserUpdate']

export function useUsers({ companyId }: { companyId?: string }) {
  return useQuery<User[], Error>({
    queryKey: ['users', companyId],
    queryFn: async () => {
      const { data, error } = await GET('/users/', {
        params: { query: { company_id: companyId } },
      })
      if (error) {
        throw new Error('Failed to fetch users')
      }
      return data.data
    },
    enabled: !!companyId, // Solo ejecutar si hay un companyId
  })
}

export function useBulkMoveAndVerifyUsers() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (data: BulkMoveRequest) => {
      const { error } = await POST('/users/bulk-move-verify', {
        body: data,
      })

      if (error) {
        throw new Error('Failed to move and verify users')
      }
    },
    onSuccess: (_, variables) => {
      // Invalidar la query de usuarios de la compañía Demo para que se refresque
      queryClient.invalidateQueries({ queryKey: ['users', variables.target_company_id] })
    },
  })
}

export function useCreateUser() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: CreateUserRequest) => {
      const { error } = await POST('/users/', { body: data })
      if (error) throw new Error('Failed to create user')
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['users', variables.company_id] })
    },
  })
}

export function useUpdateUser(userId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: UpdateUserRequest) => {
      const { error } = await PATCH('/users/{user_id}', {
        params: { path: { user_id: userId } },
        body: data,
      })
      if (error) throw new Error('Failed to update user')
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['users', variables.company_id] })
    },
  })
}

export function useUpdateUserStatus(userId: string, companyId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (isActive: boolean) => {
      const { error } = await PATCH('/users/{user_id}', {
        params: { path: { user_id: userId } },
        body: { is_active: isActive },
      })
      if (error) throw new Error('Failed to update user status')
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users', companyId] })
    },
  })
}

export function useAssignAreasToUser(userId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: { area_ids: string[] }) => {
      const { error } = await POST('/users/{user_id}/assign-areas', {
        params: { path: { user_id: userId } },
        body: data,
      })
      if (error) throw new Error('Failed to assign areas')
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] }) // Invalidamos todas las queries de usuarios
    },
  })
}
