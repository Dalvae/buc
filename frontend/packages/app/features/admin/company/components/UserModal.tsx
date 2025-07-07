import { Sheet, Button } from 'tamagui'
import { useState } from 'react'
import { UserForm } from './UserForm'
import type { User } from 'app/api/hooks/users'

interface UserModalProps {
  user?: User | null
  companyId: string
  children: React.ReactNode
  onSubmit: (data: any) => void
  isPending: boolean
}

export function UserModal({ user, companyId, children, onSubmit, isPending }: UserModalProps) {
  const [open, setOpen] = useState(false)

  const handleSubmit = (data: any) => {
    onSubmit(data)
    setOpen(false)
  }

  return (
    <Sheet
      modal
      open={open}
      onOpenChange={setOpen}
      snapPoints={[85]}
      dismissOnSnapToBottom
    >
      <Sheet.Overlay
        animation="lazy"
        enterStyle={{ o: 0 }}
        exitStyle={{ o: 0 }}
      />
      <Sheet.Handle />
      <Sheet.Frame p="$4">
        <UserForm
          user={user}
          companyId={companyId}
          onSubmit={handleSubmit}
          isPending={isPending}
        />
      </Sheet.Frame>
      <Sheet.Trigger asChild>{children}</Sheet.Trigger>
    </Sheet>
  )
}
