import { YStack, H3, Spinner, Checkbox, Label, Card } from 'tamagui'
import { useAreas } from 'app/api/hooks/areas'
import { useState, useEffect } from 'react'

interface AreaAssignmentSelectorProps {
  companyId: string
  assignedAreaIds: string[]
  onSelectionChange: (selectedIds: string[]) => void
}

export function AreaAssignmentSelector({
  companyId,
  assignedAreaIds,
  onSelectionChange,
}: AreaAssignmentSelectorProps) {
  const { data: areas, isLoading } = useAreas({ companyId })
  const [selected, setSelected] = useState<string[]>(assignedAreaIds)

  useEffect(() => {
    onSelectionChange(selected)
  }, [selected])

  const handleCheckedChange = (areaId: string, isChecked: boolean) => {
    if (isChecked) {
      setSelected((prev) => [...prev, areaId])
    } else {
      setSelected((prev) => prev.filter((id) => id !== areaId))
    }
  }

  if (isLoading) {
    return <Spinner />
  }

  return (
    <YStack space="$2">
      <H3>Asignar Áreas</H3>
      {areas?.map((area) => (
        <Card
          key={area.id}
          p="$2"
        >
          <YStack
            flexDirection="row"
            alignItems="center"
            space="$2"
          >
            <Checkbox
              id={`area-${area.id}`}
              checked={selected.includes(area.id)}
              onCheckedChange={(checked) => handleCheckedChange(area.id, !!checked)}
            >
              <Checkbox.Indicator />
            </Checkbox>
            <Label htmlFor={`area-${area.id}`}>{area.name}</Label>
          </YStack>
        </Card>
      ))}
    </YStack>
  )
}
