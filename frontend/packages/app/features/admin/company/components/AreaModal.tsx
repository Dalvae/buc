import { Sheet } from 'tamagui'
import { useState } from 'react'
import { AreaForm } from './AreaForm'
import { type Area, useCreateArea, useUpdateArea } from 'app/api/hooks/areas'

interface AreaModalProps {
  area?: Area | null
  companyId: string
  children: React.ReactNode
}

export function AreaModal({ area, companyId, children }: AreaModalProps) {
  const [open, setOpen] = useState(false)
  const { mutate: createArea, isPending: isCreating } = useCreateArea(companyId)
  const { mutate: updateArea, isPending: isUpdating } = useUpdateArea(companyId, area?.id || '')

  const isPending = isCreating || isUpdating

  const handleSubmit = (data: any) => {
    if (area) {
      updateArea(data)
    } else {
      createArea(data)
    }
    setOpen(false)
  }

  return (
    <Sheet
      modal
      open={open}
      onOpenChange={setOpen}
      snapPoints={[50]}
      dismissOnSnapToBottom
    >
      <Sheet.Overlay
        animation="lazy"
        enterStyle={{ o: 0 }}
        exitStyle={{ o: 0 }}
      />
      <Sheet.Handle />
      <Sheet.Frame p="$4">
        <AreaForm
          area={area}
          onSubmit={handleSubmit}
          isPending={isPending}
        />
      </Sheet.Frame>
      <Sheet.Trigger asChild>{children}</Sheet.Trigger>
    </Sheet>
  )
}
