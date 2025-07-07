import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import createClient from 'openapi-fetch'
import type { components } from 'app/client'

const { GET, POST } = createClient({ baseUrl: '/api/v1' })

export type AuditAssignment = components['schemas']['AuditAssignmentPublic']
export type AuditResponseCreate = components['schemas']['AuditResponseCreate']

export function useMyAuditAssignments() {
  return useQuery<AuditAssignment[], Error>({
    queryKey: ['myAuditAssignments'],
    queryFn: async () => {
      const { data, error } = await GET('/audit-assignments/my-assignments')
      if (error) throw new Error('Failed to fetch my assignments')
      // Asumiendo que la API devuelve directamente el array de asignaciones
      return data
    },
  })
}

export function useSubmitAuditResponse() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: AuditResponseCreate) => {
      const { error } = await POST('/audit-assignments/{assignment_id}/responses', {
        params: { path: { assignment_id: data.audit_assignment_id } },
        body: data,
      })
      if (error) throw new Error('Failed to submit audit response')
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['myAuditAssignments'] })
    },
  })
}
