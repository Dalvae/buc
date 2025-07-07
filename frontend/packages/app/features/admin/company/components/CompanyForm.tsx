import { Form, Button, Input, YStack, Label, Checkbox } from 'tamagui'
import { useState } from 'react'

interface CompanyFormProps {
  onSubmit: (data: any) => void
  isPending: boolean
}

export function CompanyForm({ onSubmit, isPending }: CompanyFormProps) {
  const [name, setName] = useState('')
  const [details, setDetails] = useState('')
  const [isDemo, setIsDemo] = useState(false)

  const handleSubmit = () => {
    onSubmit({ name, details, is_demo: isDemo })
  }

  return (
    <Form
      onSubmit={handleSubmit}
      space
    >
      <YStack>
        <Label htmlFor="name">Nombre de la Compañía</Label>
        <Input
          id="name"
          value={name}
          onChangeText={setName}
        />
      </YStack>
      <YStack>
        <Label htmlFor="details">Detalles</Label>
        <Input
          id="details"
          value={details}
          onChangeText={setDetails}
        />
      </YStack>
      <YStack
        flexDirection="row"
        alignItems="center"
        space
      >
        <Checkbox
          id="is_demo"
          checked={isDemo}
          onCheckedChange={setIsDemo}
        >
          <Checkbox.Indicator />
        </Checkbox>
        <Label htmlFor="is_demo">¿Es una compañía de demostración?</Label>
      </YStack>

      <Form.Trigger asChild>
        <Button
          theme="brand"
          disabled={isPending}
        >
          {isPending ? 'Creando...' : 'Crear Compañía'}
        </Button>
      </Form.Trigger>
    </Form>
  )
}
