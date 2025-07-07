import { useQuery } from '@tanstack/react-query'
import type { components } from 'app/client'
import createClient from 'openapi-fetch'

// Tipado para un usuario, basado en el schema de OpenAPI
export type User = components['schemas']['UserPublic']

const { GET } = createClient({ baseUrl: '/api/v1' })

export function useUsers() {
  return useQuery<User[], Error>({
    queryKey: ['users'],
    queryFn: async () => {
      const { data, error } = await GET('/users/')
      if (error) {
        throw new Error('Failed to fetch users')
      }
      return data.data
    },
  })
}
