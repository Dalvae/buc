import { AuthGuard } from 'app/provider/AuthGuard'
import { RespondAssignmentScreen } from 'app/features/auditor/respond-assignment'
import { useLocalSearchParams } from 'expo-router'
import { Spinner } from 'tamagui'

export default function () {
  const { id } = useLocalSearchParams()

  if (!id || typeof id !== 'string') {
    return <Spinner />
  }

  return (
    <AuthGuard>
      <RespondAssignmentScreen assignmentId={id} />
    </AuthGuard>
  )
}
