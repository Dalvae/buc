import { Button, Dialog, Paragraph, YStack } from 'tamagui'
import { useDeleteMe } from 'app/api/hooks/auth'

export function DeleteAccount() {
  const { mutate: deleteMe, isPending } = useDeleteMe()

  return (
    <Dialog>
      <Dialog.Trigger asChild>
        <Button theme="red">Eliminar Cuenta</Button>
      </Dialog.Trigger>

      <Dialog.Portal>
        <Dialog.Overlay
          key="overlay"
          animation="quick"
          o={0.5}
        />
        <Dialog.Content
          bordered
          elevate
          key="content"
          animateOnly={['transform', 'opacity']}
          animation={[
            'quick',
            {
              opacity: {
                overshootClamping: true,
              },
            },
          ]}
          enterStyle={{ x: 0, y: -20, opacity: 0, scale: 0.9 }}
          exitStyle={{ x: 0, y: 10, opacity: 0, scale: 0.95 }}
          space
        >
          <Dialog.Title>Eliminar Cuenta</Dialog.Title>
          <Dialog.Description>
            Esta acción es irreversible. ¿Estás seguro de que quieres eliminar tu cuenta?
          </Dialog.Description>
          <YStack>
            <Paragraph>Todos tus datos serán eliminados permanentemente.</Paragraph>
          </YStack>
          <Dialog.Close asChild>
            <Button
              theme="red"
              onPress={() => deleteMe()}
              disabled={isPending}
            >
              {isPending ? 'Eliminando...' : 'Sí, eliminar mi cuenta'}
            </Button>
          </Dialog.Close>
          <Dialog.Close asChild>
            <Button>Cancelar</Button>
          </Dialog.Close>
        </Dialog.Content>
      </Dialog.Portal>
    </Dialog>
  )
}
