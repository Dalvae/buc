import { YStack, H1, Spinner, Card, Paragraph, Button } from 'tamagui'
import { useCompanies } from 'app/api/hooks/companies'
import { Link } from 'solito/link'
import { CompanyModal } from './company/components/CompanyModal'

export function AdminLandingScreen() {
  const { data: companies, isLoading } = useCompanies()

  if (isLoading) {
    return <Spinner />
  }

  return (
    <YStack
      flex={1}
      space="$4"
      p="$4"
    >
      <YStack
        flexDirection="row"
        justifyContent="space-between"
        alignItems="center"
      >
        <H1>Administración</H1>
        <CompanyModal>
          <Button theme="brand">Nueva Compañía</Button>
        </CompanyModal>
      </YStack>
      <Paragraph>Selecciona una compañía para gestionar.</Paragraph>

      {companies?.map((company) => (
        <Link
          key={company.id}
          href={`/admin/company/${company.id}`}
        >
          <Card
            elevate
            size="$4"
            bordered
          >
            <Card.Header>
              <Paragraph>{company.name}</Paragraph>
            </Card.Header>
          </Card>
        </Link>
      ))}
    </YStack>
  )
}
