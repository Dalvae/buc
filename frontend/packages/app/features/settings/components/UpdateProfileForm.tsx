import { Form, Button, Input, YStack, Label, Text } from 'tamagui'
import { useUpdateMe } from 'app/api/hooks/auth'
import { useAuthStore } from 'app/store/auth'
import { useState } from 'react'

export function UpdateProfileForm() {
  const { user } = useAuthStore()
  const { mutate: updateMe, isPending, error } = useUpdateMe()
  const [fullName, setFullName] = useState(user?.full_name || '')

  const handleSubmit = () => {
    updateMe({ full_name: fullName })
  }

  return (
    <Form
      onSubmit={handleSubmit}
      space
    >
      <YStack>
        <Label htmlFor="fullName">Nombre Completo</Label>
        <Input
          id="fullName"
          value={fullName}
          onChangeText={setFullName}
          placeholder="Nombre Completo"
        />
      </YStack>

      <Form.Trigger asChild>
        <Button
          theme="brand"
          disabled={isPending}
        >
          {isPending ? 'Actualizando...' : 'Actualizar Perfil'}
        </Button>
      </Form.Trigger>

      {error && <Text color="$red10">{error.message}</Text>}
    </Form>
  )
}
