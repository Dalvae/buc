import { YStack, H1 } from 'tamagui'
import { RegisterForm } from './components/RegisterForm'

export function RegisterScreen() {
  return (
    <YStack
      flex={1}
      justifyContent="center"
      alignItems="center"
      space
    >
      <H1>Register</H1>
      <RegisterForm />
    </YStack>
  )
}
