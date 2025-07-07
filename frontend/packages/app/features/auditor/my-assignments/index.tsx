import { YStack, H1, Spinner, Card, Paragraph, XStack } from 'tamagui'
import { useMyAuditAssignments } from 'app/api/hooks/auditor'
import { Link } from 'solito/link'

export function MyAssignmentsScreen() {
  const { data: assignments, isLoading } = useMyAuditAssignments()

  if (isLoading) {
    return <Spinner />
  }

  return (
    <YStack
      flex={1}
      space="$4"
      p="$4"
    >
      <H1>Mis Asignaciones</H1>

      {assignments?.map((assignment) => (
        <Link
          key={assignment.id}
          href={`/assignment/${assignment.id}`}
        >
          <Card
            elevate
            size="$4"
            bordered
            p="$3"
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
            </XStack>
          </Card>
        </Link>
      ))}
    </YStack>
  )
}
