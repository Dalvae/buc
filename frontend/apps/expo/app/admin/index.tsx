import { AdminGuard } from 'app/provider/AdminGuard'
import { AdminLandingScreen } from 'app/features/admin'

export default function () {
  return (
    <AdminGuard>
      <AdminLandingScreen />
    </AdminGuard>
  )
}
