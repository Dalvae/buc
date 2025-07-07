import { useEffect } from 'react'
import { useColorScheme } from 'react-native'
import { DarkTheme, DefaultTheme, ThemeProvider } from '@react-navigation/native'
import { useFonts } from 'expo-font'
import { SplashScreen, Stack } from 'expo-router'
import { Provider } from 'app/provider'
import { NativeToast } from '@my/ui/src/NativeToast'

export const unstable_settings = {
  // Ensure that reloading on `/user` keeps a back button present.
  initialRouteName: 'Home',
}

// Prevent the splash screen from auto-hiding before asset loading is complete.
SplashScreen.preventAutoHideAsync()

export default function App() {
  const [interLoaded, interError] = useFonts({
    Inter: require('@tamagui/font-inter/otf/Inter-Medium.otf'),
    InterBold: require('@tamagui/font-inter/otf/Inter-Bold.otf'),
  })

  useEffect(() => {
    if (interLoaded || interError) {
      // Hide the splash screen after the fonts have loaded (or an error was returned) and the UI is ready.
      SplashScreen.hideAsync()
    }
  }, [interLoaded, interError])

  if (!interLoaded && !interError) {
    return null
  }

  return <RootLayoutNav />
}

import { ApiProvider } from 'app/provider/api'

import { useAuthStore } from 'app/store/auth'

import { ToastProvider, ToastViewport } from '@my/ui'

function RootLayoutNav() {
  const { theme } = useAuthStore()
  const { token } = useAuthStore()

  return (
    <Provider>
      <ApiProvider>
        <ToastProvider>
          <ThemeProvider value={theme === 'dark' ? DarkTheme : DefaultTheme}>
            {token ? <AppStack /> : <AuthStack />}
            <NativeToast />
            <ToastViewport />
          </ThemeProvider>
        </ToastProvider>
      </ApiProvider>
    </Provider>
  )
}

function AuthStack() {
  return (
    <Stack>
      <Stack.Screen
        name="login"
        options={{ title: 'Login' }}
      />
      <Stack.Screen
        name="register"
        options={{ title: 'Register' }}
      />
    </Stack>
  )
}

function AppStack() {
  return (
    <Stack>
      <Stack.Screen
        name="dashboard"
        options={{ title: 'Dashboard' }}
      />
      <Stack.Screen
        name="settings"
        options={{ title: 'Configuración' }}
      />
      <Stack.Screen
        name="admin"
        options={{ title: 'Administración' }}
      />
      <Stack.Screen
        name="my-assignments"
        options={{ title: 'Mis Asignaciones' }}
      />
      {/* Add other app screens here */}
    </Stack>
  )
}
