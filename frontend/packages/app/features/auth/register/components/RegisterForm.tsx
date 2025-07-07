import { Form, Button, Input, YStack, Label, Text, Select } from 'tamagui'
import { useRegister } from 'app/api/hooks/auth'
import { useCompanies } from 'app/api/hooks/companies'
import { useState } from 'react'
import { Check } from '@tamagui/lucide-icons'
import { Link } from 'solito/link'

export function RegisterForm() {
  const { mutate: register, isPending, error } = useRegister()
  const { data: companies, isLoading: isLoadingCompanies } = useCompanies()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [companyId, setCompanyId] = useState('')

  const handleSubmit = () => {
    register({ email, password, full_name: fullName, company_id: companyId })
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
      <YStack>
        <Label htmlFor="company">Compañía</Label>
        <Select
          id="company"
          value={companyId}
          onValueChange={setCompanyId}
        >
          <Select.Trigger>
            <Select.Value placeholder="Selecciona una compañía..." />
          </Select.Trigger>
          <Select.Content>
            <Select.Viewport>
              {isLoadingCompanies && (
                <Select.Item
                  index={-1}
                  value=""
                >
                  Cargando...
                </Select.Item>
              )}
              {companies?.map((company, i) => (
                <Select.Item
                  index={i}
                  key={company.id}
                  value={company.id}
                >
                  <Select.ItemText>{company.name}</Select.ItemText>
                  <Select.ItemIndicator marginLeft="auto">
                    <Check size={16} />
                  </Select.ItemIndicator>
                </Select.Item>
              ))}
            </Select.Viewport>
          </Select.Content>
        </Select>
      </YStack>

      <Form.Trigger asChild>
        <Button
          theme="brand"
          disabled={isPending}
        >
          {isPending ? 'Registrando...' : 'Registrarse'}
        </Button>
      </Form.Trigger>

      {error && <Text color="$red10">{error.message}</Text>}

      <Link href="/login">
        <Text
          ta="center"
          textDecorationLine="underline"
        >
          ¿Ya tienes una cuenta? Inicia Sesión
        </Text>
      </Link>
    </Form>
  )
}
