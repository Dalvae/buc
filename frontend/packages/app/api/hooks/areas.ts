import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import createClient from 'openapi-fetch'
import type { components } from 'app/client'

const { GET, POST, PATCH, DELETE } = createClient({ baseUrl: '/api/v1' })

export type Area = components['schemas']['AreaPublic']
export type CreateAreaRequest = components['schemas']['AreaCreate']
export type UpdateAreaRequest = components['schemas']['AreaUpdate']

export function useAreas({ companyId }: { companyId?: string }) {
  return useQuery<Area[], Error>({
    queryKey: ['areas', companyId],
    queryFn: async () => {
      const { data, error } = await GET('/companies/{company_id}/areas', {
        params: { path: { company_id: companyId! } },
      })
      if (error) throw new Error('Failed to fetch areas')
      return data.data
    },
    enabled: !!companyId,
  })
}

export function useCreateArea(companyId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: CreateAreaRequest) => {
      const { error } = await POST('/companies/{company_id}/areas', {
        params: { path: { company_id: companyId } },
        body: data,
      })
      if (error) throw new Error('Failed to create area')
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['areas', companyId] })
    },
  })
}

export function useUpdateArea(companyId: string, areaId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: UpdateAreaRequest) => {
      const { error } = await PATCH('/companies/{company_id}/areas/{area_id}', {
        params: { path: { company_id: companyId, area_id: areaId } },
        body: data,
      })
      if (error) throw new Error('Failed to update area')
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['areas', companyId] })
    },
  })
}

export function useDeleteArea(companyId: string, areaId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async () => {
      const { error } = await DELETE('/companies/{company_id}/areas/{area_id}', {
        params: { path: { company_id: companyId, area_id: areaId } },
      })
      if (error) throw new Error('Failed to delete area')
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['areas', companyId] })
    },
  })
}
