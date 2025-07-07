import { useAuthStore } from 'app/store/auth'
import { useRouter } from 'solito/router'
import { useEffect } from 'react'
import { Spinner } from 'tamagui'

export function AdminGuard({ children }: { children: React.ReactNode }) {
  const { user, status } = useAuthStore()
  const { push } = useRouter()

  const isAuthorized = user?.role === 'ADMIN' || user?.role === 'SUPERUSER'

  useEffect(() => {
    // Si ya hemos cargado el usuario y no está autorizado, lo redirigimos.
    if (status === 'authenticated' && !isAuthorized) {
      push('/dashboard')
    }
  }, [status, isAuthorized, push])

  // Mientras el estado de autenticación se resuelve, mostramos un spinner.
  if (status === 'loading' || status === 'idle') {
    return (
      <Spinner
        size="large"
        color="$brand"
      />
    )
  }

  // Si el usuario está autenticado y autorizado, mostramos el contenido.
  if (status === 'authenticated' && isAuthorized) {
    return <>{children}</>
  }

  // En cualquier otro caso (como no autenticado), no mostramos nada,
  // ya que el AuthGuard se encargará de la redirección al login.
  // O podemos mostrar un spinner para una mejor UX.
  return (
    <Spinner
      size="large"
      color="$brand"
    />
  )
}
