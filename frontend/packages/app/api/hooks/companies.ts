import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import createClient from 'openapi-fetch'
import type { components } from 'app/client'

const { GET, POST } = createClient({ baseUrl: '/api/v1' })

export type Company = components['schemas']['CompanyPublic']
export type CreateCompanyRequest = components['schemas']['CompanyCreate']

export function useCompanies() {
  return useQuery<Company[], Error>({
    queryKey: ['companies'],
    queryFn: async () => {
      const { data, error } = await GET('/companies/')
      if (error) {
        throw new Error('Failed to fetch companies')
      }
      // Suponiendo que la API devuelve un objeto con { data: [], count: 0 }
      return data.data
    },
  })
}

export function useCompany(id: string) {
  return useQuery<Company, Error>({
    queryKey: ['company', id],
    queryFn: async () => {
      const { data, error } = await GET('/companies/{company_id}', {
        params: { path: { company_id: id } },
      })
      if (error) {
        throw new Error('Failed to fetch company')
      }
      return data
    },
    enabled: !!id,
  })
}

export function useCreateCompany() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: CreateCompanyRequest) => {
      const { error } = await POST('/companies/', { body: data })
      if (error) throw new Error('Failed to create company')
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['companies'] })
    },
  })
}
