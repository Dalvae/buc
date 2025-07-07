import { YStack, H1, Separator, H3 } from 'tamagui'
import { ThemeSwitcher } from './components/ThemeSwitcher'
import { UpdateProfileForm } from './components/UpdateProfileForm'
import { DeleteAccount } from './components/DeleteAccount'

export function SettingsScreen() {
  return (
    <YStack
      flex={1}
      space="$4"
      p="$4"
    >
      <H1>Configuración</H1>
      <Separator />

      <H3>Tema</H3>
      <ThemeSwitcher />

      <Separator />

      <H3>Perfil</H3>
      <UpdateProfileForm />

      <Separator />

      <H3>Cuenta</H3>
      <DeleteAccount />
    </YStack>
  )
}
