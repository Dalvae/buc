import { AdminGuard } from 'app/provider/AdminGuard'
import { CompanyDashboardScreen } from 'app/features/admin/company'
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
      <CompanyDashboardScreen id={id} />
    </AdminGuard>
  )
}
