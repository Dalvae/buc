import { YStack, H2, Spinner, Card, Button, XStack, Paragraph } from 'tamagui'
import { useAreas, useDeleteArea } from 'app/api/hooks/areas'
import { AreaModal } from './AreaModal'

export function AreaManagementView({ companyId }: { companyId: string }) {
  const { data: areas, isLoading } = useAreas({ companyId })

  if (isLoading) {
    return <Spinner />
  }

  return (
    <YStack space="$4">
      <H2>Áreas de la Compañía</H2>
      <AreaModal companyId={companyId}>
        <Button theme="brand">Nueva Área</Button>
      </AreaModal>

      {areas?.map((area) => (
        <Card
          key={area.id}
          p="$3"
          bordered
        >
          <XStack
            justifyContent="space-between"
            alignItems="center"
          >
            <YStack>
              <Paragraph fontWeight="bold">{area.name}</Paragraph>
              <Paragraph
                fontSize="$2"
                color="$gray10"
              >
                {area.description}
              </Paragraph>
            </YStack>
            <XStack space="$2">
              <AreaModal
                companyId={companyId}
                area={area}
              >
                <Button size="$2">Editar</Button>
              </AreaModal>
              <Button
                size="$2"
                theme="red"
                onPress={() => useDeleteArea(companyId, area.id).mutate()}
                disabled={useDeleteArea(companyId, area.id).isPending}
              >
                Eliminar
              </Button>
            </XStack>
          </XStack>
        </Card>
      ))}
    </YStack>
  )
}
