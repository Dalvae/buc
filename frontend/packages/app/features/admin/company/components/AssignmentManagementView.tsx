import { YStack, H2, Spinner, Card, Button, XStack, Paragraph } from 'tamagui'
import { useAuditAssignments, useDeleteAssignment } from 'app/api/hooks/auditAssignments'
import { Link } from 'solito/link'

export function AssignmentManagementView({ companyId }: { companyId: string }) {
  const { data: assignments, isLoading } = useAuditAssignments({ companyId })

  if (isLoading) {
    return <Spinner />
  }

  return (
    <YStack space="$4">
      <H2>Asignaciones de Auditoría</H2>
      <Link href={`/admin/company/${companyId}/assignments/new`}>
        <Button theme="brand">Nueva Asignación</Button>
      </Link>

      {assignments?.map((assignment) => (
        <Card
          key={assignment.id}
          p="$3"
          bordered
        >
          <XStack
            justifyContent="space-between"
            alignItems="center"
          >
            <YStack>
              <Paragraph fontWeight="bold">{assignment.title}</Paragraph>
              <Paragraph
                fontSize="$2"
                color="$gray10"
              >
                Estado: {assignment.status}
              </Paragraph>
              <Paragraph
                fontSize="$2"
                color="$gray10"
              >
                Vence:{' '}
                {assignment.due_date ? new Date(assignment.due_date).toLocaleDateString() : 'N/A'}
              </Paragraph>
            </YStack>
            <XStack space="$2">
              <Button size="$2">Editar</Button>
              <Button
                size="$2"
                theme="red"
                onPress={() => useDeleteAssignment(assignment.id, companyId).mutate()}
                disabled={useDeleteAssignment(assignment.id, companyId).isPending}
              >
                Eliminar
              </Button>
            </XStack>
          </XStack>
        </Card>
      ))}
    </YStack>
  )
}
