import {
  YStack,
  H1,
  Spinner,
  Select,
  Paragraph,
  Input,
  Textarea,
  Button,
  Card,
  Separator,
} from 'tamagui'
import { useReducer, useEffect } from 'react'
import { useAuditTemplates, useAuditTemplate } from 'app/api/hooks/auditTemplates'
import { useCreateAssignment } from 'app/api/hooks/auditAssignments'
import { useRouter } from 'solito/router'

const initialState = {
  templateId: null,
  title: '',
  description: '',
  dueDate: '',
  questions: [],
}

function reducer(state, action) {
  switch (action.type) {
    case 'SET_TEMPLATE':
      return {
        ...state,
        templateId: action.payload.id,
        title: action.payload.name,
        description: action.payload.description,
        questions: action.payload.question_templates || [],
      }
    case 'UPDATE_FIELD':
      return { ...state, [action.payload.field]: action.payload.value }
    case 'UPDATE_QUESTION_TEXT':
      return {
        ...state,
        questions: state.questions.map((q, index) =>
          index === action.payload.index ? { ...q, text: action.payload.text } : q
        ),
      }
    default:
      return state
  }
}

export function CreateAssignmentScreen({ companyId }: { companyId: string }) {
  const [state, dispatch] = useReducer(reducer, initialState)
  const { data: templates, isLoading: isLoadingTemplates } = useAuditTemplates()
  const { data: selectedTemplate, isLoading: isLoadingTemplate } = useAuditTemplate(
    state.templateId
  )
  const { mutate: createAssignment, isPending } = useCreateAssignment(companyId)
  const router = useRouter()

  useEffect(() => {
    if (selectedTemplate) {
      dispatch({ type: 'SET_TEMPLATE', payload: selectedTemplate })
    }
  }, [selectedTemplate])

  const handleSave = () => {
    const assignmentData = { ...state, company_id: companyId }
    createAssignment(assignmentData, {
      onSuccess: () => {
        router.back()
      },
    })
  }

  return (
    <YStack
      flex={1}
      space="$4"
      p="$4"
    >
      <H1>Nueva Asignación de Auditoría</H1>

      <Paragraph>Paso 1: Selecciona una Plantilla</Paragraph>
      <Select
        onValueChange={(id) =>
          dispatch({ type: 'UPDATE_FIELD', payload: { field: 'templateId', value: id } })
        }
      >
        <Select.Trigger>
          <Select.Value placeholder="Selecciona una plantilla..." />
        </Select.Trigger>
        <Select.Content>
          <Select.Viewport>
            {isLoadingTemplates && (
              <Select.Item
                index={-1}
                value=""
              >
                Cargando...
              </Select.Item>
            )}
            {templates?.map((template, i) => (
              <Select.Item
                index={i}
                key={template.id}
                value={template.id}
              >
                <Select.ItemText>{template.name}</Select.ItemText>
              </Select.Item>
            ))}
          </Select.Viewport>
        </Select.Content>
      </Select>

      {(isLoadingTemplate || state.templateId) && <Spinner />}

      {state.templateId && !isLoadingTemplate && (
        <>
          <Separator />
          <Paragraph>Paso 2: Personaliza los Detalles</Paragraph>
          <Input
            placeholder="Título Descriptivo"
            value={state.title}
            onChangeText={(text) =>
              dispatch({ type: 'UPDATE_FIELD', payload: { field: 'title', value: text } })
            }
          />
          <Input
            placeholder="Descripción"
            value={state.description}
            onChangeText={(text) =>
              dispatch({ type: 'UPDATE_FIELD', payload: { field: 'description', value: text } })
            }
            multiline
            numberOfLines={4}
          />
          {/* Calendario para Due Date */}

          <Separator />
          <Paragraph>Paso 3: Edita las Preguntas (Opcional)</Paragraph>
          {state.questions.map((q, index) => (
            <Card
              key={index}
              p="$2"
            >
              <Input
                value={q.text}
                onChangeText={(text) =>
                  dispatch({ type: 'UPDATE_QUESTION_TEXT', payload: { index, text } })
                }
                multiline
              />
            </Card>
          ))}

          <Button
            theme="brand"
            onPress={handleSave}
            disabled={isPending}
          >
            {isPending ? 'Guardando...' : 'Guardar y Asignar'}
          </Button>
        </>
      )}
    </YStack>
  )
}
