import { YStack, Label, Switch } from 'tamagui'
import { useAuthStore } from 'app/store/auth'

export function ThemeSwitcher() {
  const { theme, setTheme } = useAuthStore()
  const isDark = theme === 'dark'

  const handleCheckedChange = (checked: boolean) => {
    setTheme(checked ? 'dark' : 'light')
  }

  return (
    <YStack
      space="$2"
      flexDirection="row"
      alignItems="center"
    >
      <Label
        htmlFor="theme-switch"
        pr="$2"
      >
        Tema Oscuro
      </Label>
      <Switch
        id="theme-switch"
        checked={isDark}
        onCheckedChange={handleCheckedChange}
      >
        <Switch.Thumb animation="bouncy" />
      </Switch>
    </YStack>
  )
}
