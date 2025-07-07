import {
  YStack,
  Label,
  Input,
  Select,
  Checkbox,
  Paragraph,
  Card,
  Slider,
  H3,
  Separator,
} from 'tamagui'
import type { components } from 'app/client'
import { useState } from 'react'

type Question = components['schemas']['AssignedQuestionPublic']

interface QuestionRendererProps {
  question: Question
  onAnswerChange: (answer: any) => void
}

export function QuestionRenderer({ question, onAnswerChange }: QuestionRendererProps) {
  const [selectedOptions, setSelectedOptions] = useState<string[]>([])

  const handleMultiChoiceChange = (option: string, isSelected: boolean) => {
    const newSelection = isSelected
      ? [...selectedOptions, option]
      : selectedOptions.filter((o) => o !== option)
    setSelectedOptions(newSelection)
    onAnswerChange(newSelection)
  }

  const renderQuestion = () => {
    switch (question.question_type) {
      case 'TEXT':
        return <Input onChangeText={onAnswerChange} />
      case 'YES_NO':
        return (
          <Checkbox onCheckedChange={(checked) => onAnswerChange(checked ? 'Yes' : 'No')}>
            <Checkbox.Indicator />
          </Checkbox>
        )
      case 'MULTIPLE_CHOICE_SINGLE':
        return (
          <Select onValueChange={onAnswerChange}>
            <Select.Trigger>
              <Select.Value placeholder="Selecciona una opción..." />
            </Select.Trigger>
            <Select.Content>
              <Select.Viewport>
                {question.options?.map((option, i) => (
                  <Select.Item
                    index={i}
                    key={option}
                    value={option}
                  >
                    <Select.ItemText>{option}</Select.ItemText>
                  </Select.Item>
                ))}
              </Select.Viewport>
            </Select.Content>
          </Select>
        )
      case 'MULTIPLE_CHOICE_MULTIPLE':
        return (
          <YStack space="$2">
            {question.options?.map((option) => (
              <YStack
                key={option}
                flexDirection="row"
                alignItems="center"
                space="$2"
              >
                <Checkbox
                  id={`q-${question.id}-opt-${option}`}
                  onCheckedChange={(checked) => handleMultiChoiceChange(option, !!checked)}
                >
                  <Checkbox.Indicator />
                </Checkbox>
                <Label htmlFor={`q-${question.id}-opt-${option}`}>{option}</Label>
              </YStack>
            ))}
          </YStack>
        )
      case 'RATING_SCALE':
        return (
          <Slider
            defaultValue={[5]}
            max={10}
            step={1}
            onValueChange={(value) => onAnswerChange(value[0])}
          >
            <Slider.Track>
              <Slider.TrackActive />
            </Slider.Track>
            <Slider.Thumb
              circular
              index={0}
            />
          </Slider>
        )
      case 'SECTION_HEADER':
        return null // No es un input, se maneja fuera del switch
      default:
        return <Paragraph>Tipo de pregunta no soportado: {question.question_type}</Paragraph>
    }
  }

  if (question.question_type === 'SECTION_HEADER') {
    return (
      <YStack
        space="$2"
        pt="$4"
      >
        <H3>{question.text}</H3>
        <Separator />
      </YStack>
    )
  }

  return (
    <Card
      p="$3"
      bordered
    >
      <YStack space="$2">
        <Label>{question.text}</Label>
        {renderQuestion()}
      </YStack>
    </Card>
  )
}
