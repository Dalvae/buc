import { AdminGuard } from 'app/provider/AdminGuard'
import { CompanyDashboardScreen } from 'app/features/admin/company'
import { useLocalSearchParams } from 'expo-router'
import { Spinner } from 'tamagui'

export default function () {
  const { id } = useLocalSearchParams()

  if (!id || typeof id !== 'string') {
    return <Spinner />
  }

  return (
    <AdminGuard>
      <CompanyDashboardScreen id={id} />
    </AdminGuard>
  )
}
