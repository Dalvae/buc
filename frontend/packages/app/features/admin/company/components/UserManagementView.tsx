import { YStack, H2, Spinner, Paragraph, Card, Button, XStack, Dialog } from 'tamagui'
import { useUsers, useCreateUser, useUpdateUser, useUpdateUserStatus } from 'app/api/hooks/users'
import { UserModal } from './UserModal'

export function UserManagementView({ companyId }: { companyId: string }) {
  const { data: users, isLoading } = useUsers({ companyId })
  const { mutate: createUser, isPending: isCreating } = useCreateUser()

  return (
    <YStack space="$4">
      <H2>Usuarios de la Compañía</H2>
      <UserModal
        companyId={companyId}
        onSubmit={(data) => createUser({ ...data, company_id: companyId })}
        isPending={isCreating}
      >
        <Button theme="brand">Añadir Usuario</Button>
      </UserModal>

      {isLoading && <Spinner />}

      {users?.map((user) => {
        const { mutate: updateUserStatus, isPending: isUpdatingStatus } = useUpdateUserStatus(
          user.id,
          companyId
        )
        return (
          <Card
            key={user.id}
            p="$3"
            bordered
          >
            <XStack
              justifyContent="space-between"
              alignItems="center"
            >
              <YStack>
                <Paragraph fontWeight="bold">{user.full_name}</Paragraph>
                <Paragraph>{user.email}</Paragraph>
                <Paragraph
                  fontSize="$2"
                  color="$gray10"
                >
                  Rol: {user.role}
                </Paragraph>
                <Paragraph
                  fontSize="$2"
                  color={user.is_active ? '$green10' : '$red10'}
                >
                  {user.is_active ? 'Activo' : 'Inactivo'}
                </Paragraph>
              </YStack>
              <XStack space="$2">
                <UserModal
                  user={user}
                  companyId={companyId}
                  onSubmit={(data) =>
                    useUpdateUser(user.id).mutate({ ...data, company_id: companyId })
                  }
                  isPending={useUpdateUser(user.id).isPending}
                >
                  <Button size="$2">Editar</Button>
                </UserModal>
                <Dialog>
                  <Dialog.Trigger asChild>
                    <Button
                      size="$2"
                      theme={user.is_active ? 'red' : 'green'}
                    >
                      {user.is_active ? 'Desactivar' : 'Activar'}
                    </Button>
                  </Dialog.Trigger>
                  <Dialog.Portal>
                    <Dialog.Overlay />
                    <Dialog.Content>
                      <Dialog.Title>Confirmar Acción</Dialog.Title>
                      <Dialog.Description>
                        ¿Estás seguro de que quieres {user.is_active ? 'desactivar' : 'activar'} a
                        este usuario?
                      </Dialog.Description>
                      <Dialog.Close asChild>
                        <Button
                          onPress={() => updateUserStatus(!user.is_active)}
                          disabled={isUpdatingStatus}
                        >
                          Confirmar
                        </Button>
                      </Dialog.Close>
                    </Dialog.Content>
                  </Dialog.Portal>
                </Dialog>
              </XStack>
            </XStack>
          </Card>
        )
      })}
    </YStack>
  )
}
