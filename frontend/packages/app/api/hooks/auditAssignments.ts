import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import createClient from 'openapi-fetch'
import type { components } from 'app/client'

const { GET, POST, PATCH, DELETE } = createClient({ baseUrl: '/api/v1' })

export type AuditAssignment = components['schemas']['AuditAssignmentPublic']
export type CreateAssignmentRequest = components['schemas']['AuditAssignmentCreate']
export type UpdateAssignmentRequest = components['schemas']['AuditAssignmentUpdate']

export function useAuditAssignments({ companyId }: { companyId?: string }) {
  return useQuery<AuditAssignment[], Error>({
    queryKey: ['auditAssignments', companyId],
    queryFn: async () => {
      const { data, error } = await GET('/audit-assignments/company/{company_id}', {
        params: { path: { company_id: companyId! } },
      })
      if (error) throw new Error('Failed to fetch assignments')
      return data.data
    },
    enabled: !!companyId,
  })
}

export function useCreateAssignment(companyId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: CreateAssignmentRequest) => {
      const { error } = await POST('/audit-assignments/', { body: data })
      if (error) throw new Error('Failed to create assignment')
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['auditAssignments', companyId] })
    },
  })
}

export function useUpdateAssignment(assignmentId: string, companyId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async (data: UpdateAssignmentRequest) => {
      const { error } = await PATCH('/audit-assignments/{assignment_id}', {
        params: { path: { assignment_id: assignmentId } },
        body: data,
      })
      if (error) throw new Error('Failed to update assignment')
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['auditAssignments', companyId] })
    },
  })
}

export function useDeleteAssignment(assignmentId: string, companyId: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async () => {
      const { error } = await DELETE('/audit-assignments/{assignment_id}', {
        params: { path: { assignment_id: assignmentId } },
      })
      if (error) throw new Error('Failed to delete assignment')
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['auditAssignments', companyId] })
    },
  })
}

export function useAuditAssignment(assignmentId: string) {
  return useQuery<AuditAssignment, Error>({
    queryKey: ['auditAssignment', assignmentId],
    queryFn: async () => {
      const { data, error } = await GET('/audit-assignments/{assignment_id}', {
        params: { path: { assignment_id: assignmentId } },
      })
      if (error) throw new Error('Failed to fetch assignment')
      return data
    },
    enabled: !!assignmentId,
  })
}
