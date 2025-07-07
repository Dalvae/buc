import { Form, Button, Input, YStack, Label } from 'tamagui'
import { useState, useEffect } from 'react'
import type { Area } from 'app/api/hooks/areas'

interface AreaFormProps {
  area?: Area | null
  onSubmit: (data: any) => void
  isPending: boolean
}

export function AreaForm({ area, onSubmit, isPending }: AreaFormProps) {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')

  useEffect(() => {
    if (area) {
      setName(area.name)
      setDescription(area.description || '')
    }
  }, [area])

  const handleSubmit = () => {
    onSubmit({ name, description })
  }

  return (
    <Form
      onSubmit={handleSubmit}
      space
    >
      <YStack>
        <Label htmlFor="name">Nombre del Área</Label>
        <Input
          id="name"
          value={name}
          onChangeText={setName}
        />
      </YStack>
      <YStack>
        <Label htmlFor="description">Descripción</Label>
        <Input
          id="description"
          value={description}
          onChangeText={setDescription}
        />
      </YStack>

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
