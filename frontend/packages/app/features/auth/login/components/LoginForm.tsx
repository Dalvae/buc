import { Form, Button, Input, YStack, Label, Text } from 'tamagui'
import { useLogin } from 'app/api/hooks/auth'
import { useState } from 'react'
import { Link } from 'solito/link'

export function LoginForm() {
  const { mutate: login, isPending, error } = useLogin()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const handleSubmit = () => {
    login({ username: email, password })
  }

  return (
    <Form
      onSubmit={handleSubmit}
      space
    >
      <YStack>
        <Label htmlFor="email">Correo Electrónico</Label>
        <Input
          id="email"
          value={email}
          onChangeText={setEmail}
          placeholder="Correo Electrónico"
          autoCapitalize="none"
        />
      </YStack>
      <YStack>
        <Label htmlFor="password">Contraseña</Label>
        <Input
          id="password"
          value={password}
          onChangeText={setPassword}
          placeholder="Contraseña"
          secureTextEntry
        />
      </YStack>

      <Form.Trigger asChild>
        <Button
          theme="brand"
          disabled={isPending}
        >
          {isPending ? 'Iniciando sesión...' : 'Iniciar Sesión'}
        </Button>
      </Form.Trigger>

      {error && <Text color="$red10">{error.message}</Text>}

      <Link href="/register">
        <Text
          ta="center"
          textDecorationLine="underline"
        >
          ¿No tienes una cuenta? Regístrate
        </Text>
      </Link>
    </Form>
  )
}
