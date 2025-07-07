import { useAuthStore } from 'app/store/auth'
import { useRouter } from 'solito/router'
import { useEffect } from 'react'
import { Spinner } from 'tamagui'

const publicRoutes = ['/login', '/register']

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { status, token } = useAuthStore()
  const { push, pathname } = useRouter()

  useEffect(() => {
    if (status === 'idle') {
      // Aún no sabemos si está autenticado, podríamos leer el token de localStorage aquí
      // Por ahora, si no hay token, lo mandamos a unauthenticated
      if (!token) {
        useAuthStore.setState({ status: 'unauthenticated' })
      }
    }

    if (status === 'unauthenticated' && !publicRoutes.includes(pathname)) {
      push('/login')
    }

    if (status === 'authenticated' && publicRoutes.includes(pathname)) {
      push('/dashboard')
    }
  }, [status, pathname, token, push])

  if (status === 'idle' || status === 'loading') {
    return (
      <Spinner
        size="large"
        color="$brand"
      />
    )
  }

  if (status === 'authenticated' && publicRoutes.includes(pathname)) {
    return (
      <Spinner
        size="large"
        color="$brand"
      />
    )
  }

  if (status === 'unauthenticated' && !publicRoutes.includes(pathname)) {
    return (
      <Spinner
        size="large"
        color="$brand"
      />
    )
  }

  return <>{children}</>
}
