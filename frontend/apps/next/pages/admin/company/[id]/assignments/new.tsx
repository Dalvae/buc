import { AdminGuard } from 'app/provider/AdminGuard'
import { CreateAssignmentScreen } from 'app/features/admin/assignments'
import { useRouter } from 'solito/router'
import { Spinner } from 'tamagui'

export default function () {
  const { query } = useRouter()
  const id = query.id as string

  if (!id) {
    return <Spinner />
  }

  return (
    <AdminGuard>
      <CreateAssignmentScreen companyId={id} />
    </AdminGuard>
  )
}
