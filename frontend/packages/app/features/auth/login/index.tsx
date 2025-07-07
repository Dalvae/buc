import { YStack, H1 } from 'tamagui'
import { LoginForm } from './components/LoginForm'

export function LoginScreen() {
  return (
    <YStack
      flex={1}
      justifyContent="center"
      alignItems="center"
      space
    >
      <H1>Login</H1>
      <LoginForm />
    </YStack>
  )
}
