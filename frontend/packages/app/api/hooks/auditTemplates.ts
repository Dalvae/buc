import { useQuery } from '@tanstack/react-query'
import createClient from 'openapi-fetch'
import type { components } from 'app/client'

const { GET } = createClient({ baseUrl: '/api/v1' })

export type AuditTemplate = components['schemas']['AuditTemplatePublic']

export function useAuditTemplates() {
  return useQuery<AuditTemplate[], Error>({
    queryKey: ['auditTemplates'],
    queryFn: async () => {
      const { data, error } = await GET('/audit-templates/')
      if (error) throw new Error('Failed to fetch audit templates')
      return data.data
    },
  })
}

export function useAuditTemplate(templateId: string | null) {
  return useQuery<AuditTemplate, Error>({
    queryKey: ['auditTemplate', templateId],
    queryFn: async () => {
      const { data, error } = await GET('/audit-templates/{template_id}', {
        params: { path: { template_id: templateId! } },
      })
      if (error) throw new Error('Failed to fetch audit template')
      return data
    },
    enabled: !!templateId,
  })
}
