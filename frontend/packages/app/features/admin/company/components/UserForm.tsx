import { Form, Button, Input, YStack, Label, Select, Paragraph, Separator } from 'tamagui'
import { useState, useEffect } from 'react'
import type { User } from 'app/api/hooks/users'
import { AreaAssignmentSelector } from './AreaAssignmentSelector'
import { useAssignAreasToUser } from 'app/api/hooks/users'

interface UserFormProps {
  user?: User | null
  companyId: string
  onSubmit: (data: any) => void
  isPending: boolean
}

export function UserForm({ user, companyId, onSubmit, isPending }: UserFormProps) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [role, setRole] = useState('USER')
  const [selectedAreaIds, setSelectedAreaIds] = useState<string[]>([])

  const { mutate: assignAreas } = useAssignAreasToUser(user?.id || '')

  useEffect(() => {
    if (user) {
      setEmail(user.email)
      setFullName(user.full_name || '')
      setRole(user.role)
      // Suponiendo que el objeto User tiene un array `assigned_areas` con los IDs
      setSelectedAreaIds(user.assigned_areas?.map((a) => a.id) || [])
    }
  }, [user])

  const handleSubmit = () => {
    const data = { email, full_name: fullName, role, ...(password && { password }) }
    onSubmit(data)
    if (user) {
      assignAreas({ area_ids: selectedAreaIds })
    }
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
        />
      </YStack>
      <YStack>
        <Label htmlFor="email">Correo Electrónico</Label>
        <Input
          id="email"
          value={email}
          onChangeText={setEmail}
          autoCapitalize="none"
        />
      </YStack>
      {!user && (
        <YStack>
          <Label htmlFor="password">Contraseña</Label>
          <Input
            id="password"
            value={password}
            onChangeText={setPassword}
            secureTextEntry
          />
        </YStack>
      )}
      <YStack>
        <Label htmlFor="role">Rol</Label>
        <Select
          id="role"
          value={role}
          onValueChange={setRole}
        >
          <Select.Trigger>
            <Select.Value />
          </Select.Trigger>
          <Select.Content>
            <Select.Viewport>
              <Select.Item
                index={0}
                value="USER"
              >
                <Select.ItemText>Usuario</Select.ItemText>
              </Select.Item>
              <Select.Item
                index={1}
                value="AUDITOR"
              >
                <Select.ItemText>Auditor</Select.ItemText>
              </Select.Item>
              <Select.Item
                index={2}
                value="ADMIN"
              >
                <Select.ItemText>Administrador</Select.ItemText>
              </Select.Item>
            </Select.Viewport>
          </Select.Content>
        </Select>
      </YStack>

      {user && (
        <>
          <Separator />
          <AreaAssignmentSelector
            companyId={companyId}
            assignedAreaIds={selectedAreaIds}
            onSelectionChange={setSelectedAreaIds}
          />
        </>
      )}

      <Form.Trigger asChild>
        <Button
          theme="brand"
          disabled={isPending}
        >
          {isPending ? 'Guardando...' : 'Guardar'}
        </Button>
      </Form.Trigger>
    </Form>
  )
}
