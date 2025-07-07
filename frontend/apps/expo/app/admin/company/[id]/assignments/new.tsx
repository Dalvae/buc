import { AdminGuard } from 'app/provider/AdminGuard'
import { CreateAssignmentScreen } from 'app/features/admin/assignments'
import { useLocalSearchParams } from 'expo-router'
import { Spinner } from 'tamagui'

export default function () {
  const { id } = useLocalSearchParams()

  if (!id || typeof id !== 'string') {
    return <Spinner />
  }

  return (
    <AdminGuard>
      <CreateAssignmentScreen companyId={id} />
    </AdminGuard>
  )
}
