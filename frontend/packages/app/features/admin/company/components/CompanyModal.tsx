import { Sheet } from 'tamagui'
import { useState } from 'react'
import { CompanyForm } from './CompanyForm'
import { useCreateCompany } from 'app/api/hooks/companies'

interface CompanyModalProps {
  children: React.ReactNode
}

export function CompanyModal({ children }: CompanyModalProps) {
  const [open, setOpen] = useState(false)
  const { mutate: createCompany, isPending } = useCreateCompany()

  const handleSubmit = (data: any) => {
    createCompany(data, {
      onSuccess: () => setOpen(false),
    })
  }

  return (
    <Sheet
      modal
      open={open}
      onOpenChange={setOpen}
      snapPoints={[60]}
      dismissOnSnapToBottom
    >
      <Sheet.Overlay
        animation="lazy"
        enterStyle={{ o: 0 }}
        exitStyle={{ o: 0 }}
      />
      <Sheet.Handle />
      <Sheet.Frame p="$4">
        <CompanyForm
          onSubmit={handleSubmit}
          isPending={isPending}
        />
      </Sheet.Frame>
      <Sheet.Trigger asChild>{children}</Sheet.Trigger>
    </Sheet>
  )
}
