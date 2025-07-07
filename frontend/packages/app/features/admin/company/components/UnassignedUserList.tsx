import { YStack, H2, Spinner, Paragraph, Checkbox, Card } from 'tamagui'
import { useUsers } from 'app/api/hooks/users'
import { useState } from 'react'
import { BulkActions } from './BulkActions'

export function UnassignedUserList({ companyId }: { companyId: string }) {
  const { data: users, isLoading } = useUsers({ companyId })
  const [selectedUsers, setSelectedUsers] = useState<string[]>([])

  const handleSelectUser = (userId: string, isSelected: boolean) => {
    if (isSelected) {
      setSelectedUsers((prev) => [...prev, userId])
    } else {
      setSelectedUsers((prev) => prev.filter((id) => id !== userId))
    }
  }

  if (isLoading) {
    return <Spinner />
  }

  return (
    <YStack space="$4">
      <H2>Usuarios Pendientes</H2>
      <BulkActions selectedUsers={selectedUsers} />

      {users?.map((user) => (
        <Card
          key={user.id}
          p="$2"
        >
          <YStack
            flexDirection="row"
            alignItems="center"
            space="$2"
          >
            <Checkbox
              id={`user-${user.id}`}
              onCheckedChange={(checked) => handleSelectUser(user.id, !!checked)}
            >
              <Checkbox.Indicator />
            </Checkbox>
            <Paragraph>{user.full_name || user.email}</Paragraph>
          </YStack>
        </Card>
      ))}
    </YStack>
  )
}
