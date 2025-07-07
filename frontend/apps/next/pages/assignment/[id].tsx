import { AuthGuard } from 'app/provider/AuthGuard'
import { RespondAssignmentScreen } from 'app/features/auditor/respond-assignment'
import { useRouter } from 'solito/router'
import { Spinner } from 'tamagui'

export default function () {
  const { query } = useRouter()
  const id = query.id as string

  if (!id) {
    return <Spinner />
  }

  return (
    <AuthGuard>
      <RespondAssignmentScreen assignmentId={id} />
    </AuthGuard>
  )
}
