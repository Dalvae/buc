import { YStack, H1, Spinner, Paragraph, Button, Input } from 'tamagui'
import { useAuditAssignment } from 'app/api/hooks/auditAssignments'
import { useReducer } from 'react'
import { QuestionRenderer } from './components/QuestionRenderer'
import { useSubmitAuditResponse } from 'app/api/hooks/auditor'
import { useRouter } from 'solito/router'

const initialState = {
  answers: {},
  overall_comments: '',
}

function reducer(state, action) {
  switch (action.type) {
    case 'SET_ANSWER':
      return {
        ...state,
        answers: {
          ...state.answers,
          [action.payload.questionId]: { answer_value: action.payload.answer },
        },
      }
    case 'SET_OVERALL_COMMENTS':
      return { ...state, overall_comments: action.payload.comments }
    default:
      return state
  }
}

export function RespondAssignmentScreen({ assignmentId }: { assignmentId: string }) {
  const { data: assignment, isLoading } = useAuditAssignment(assignmentId)
  const [state, dispatch] = useReducer(reducer, initialState)
  const { mutate: submitResponse, isPending } = useSubmitAuditResponse()
  const router = useRouter()

  const handleSubmit = () => {
    const answers = Object.entries(state.answers).map(([questionId, answer]) => ({
      assigned_question_id: questionId,
      ...answer,
    }))
    const responseData = {
      answers,
      overall_comments: state.overall_comments,
      audit_assignment_id: assignmentId,
    }
    submitResponse(responseData, {
      onSuccess: () => {
        router.back()
      },
    })
  }

  if (isLoading) {
    return <Spinner />
  }

  if (!assignment) {
    return <Paragraph>Asignación no encontrada.</Paragraph>
  }

  return (
    <YStack
      flex={1}
      space="$4"
      p="$4"
    >
      <H1>{assignment.title}</H1>
      <Paragraph>{assignment.description}</Paragraph>

      {assignment.assigned_questions?.map((question) => (
        <QuestionRenderer
          key={question.id}
          question={question}
          onAnswerChange={(answer) =>
            dispatch({ type: 'SET_ANSWER', payload: { questionId: question.id, answer } })
          }
        />
      ))}

      <Input
        placeholder="Comentarios generales..."
        onChangeText={(text) =>
          dispatch({ type: 'SET_OVERALL_COMMENTS', payload: { comments: text } })
        }
        multiline
        numberOfLines={4}
      />

      <Button
        theme="brand"
        onPress={handleSubmit}
        disabled={isPending}
      >
        {isPending ? 'Enviando...' : 'Enviar Respuestas'}
      </Button>
    </YStack>
  )
}
