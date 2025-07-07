import { Button, Dialog, Select, YStack } from 'tamagui'
import { useCompanies } from 'app/api/hooks/companies'
import { useState } from 'react'
import { Check } from '@tamagui/lucide-icons'
import { useBulkMoveAndVerifyUsers } from 'app/api/hooks/users'

export function BulkActions({ selectedUsers }: { selectedUsers: string[] }) {
  const { data: companies, isLoading: isLoadingCompanies } = useCompanies()
  const { mutate: moveAndVerify, isPending } = useBulkMoveAndVerifyUsers()
  const [targetCompanyId, setTargetCompanyId] = useState('')

  const handleMoveAndVerify = () => {
    moveAndVerify({ user_ids: selectedUsers, target_company_id: targetCompanyId })
  }

  return (
    <Dialog>
      <Dialog.Trigger asChild>
        <Button disabled={selectedUsers.length === 0}>
          Mover y Verificar ({selectedUsers.length})
        </Button>
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
          animation={['quick', { opacity: { overshootClamping: true } }]}
          enterStyle={{ x: 0, y: -20, opacity: 0, scale: 0.9 }}
          exitStyle={{ x: 0, y: 10, opacity: 0, scale: 0.95 }}
          space
        >
          <Dialog.Title>Mover y Verificar Usuarios</Dialog.Title>
          <Dialog.Description>
            Selecciona la compañía de destino para los {selectedUsers.length} usuarios
            seleccionados.
          </Dialog.Description>

          <YStack>
            <Select
              id="company"
              value={targetCompanyId}
              onValueChange={setTargetCompanyId}
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

          <Dialog.Close asChild>
            <Button
              theme="brand"
              onPress={handleMoveAndVerify}
              disabled={isPending}
            >
              {isPending ? 'Moviendo...' : 'Confirmar'}
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
