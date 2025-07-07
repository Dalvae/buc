import { YStack, H1, Button, Text } from 'tamagui'
import { useAuthStore } from 'app/store/auth'
import { Link } from 'solito/link'

export function DashboardScreen() {
  const { logout, user } = useAuthStore()
  const isAdmin = user?.role === 'ADMIN' || user?.role === 'SUPERUSER'
  const isAuditor = user?.role === 'AUDITOR'

  return (
    <YStack
      flex={1}
      justifyContent="center"
      alignItems="center"
      space
    >
      <H1>Panel de Control</H1>
      {user && <Text>Bienvenido, {user.full_name || user.email}</Text>}

      {isAdmin && (
        <Link href="/admin">
          <Button>Administración</Button>
        </Link>
      )}

      {isAuditor && (
        <Link href="/my-assignments">
          <Button>Mis Asignaciones</Button>
        </Link>
      )}

      <Link href="/settings">
        <Button>Ir a Configuración</Button>
      </Link>
      <Button
        onPress={logout}
        theme="brand"
      >
        Cerrar Sesión
      </Button>
    </YStack>
  )
}
