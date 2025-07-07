import { YStack, H1, Spinner, Tabs, Paragraph } from 'tamagui'
import { useCompany } from 'app/api/hooks/companies'
import { useAuthStore } from 'app/store/auth'
import { UnassignedUserList } from './components/UnassignedUserList'
import { UserManagementView } from './components/UserManagementView'
import { AreaManagementView } from './components/AreaManagementView'
import { AssignmentManagementView } from './components/AssignmentManagementView'

export function CompanyDashboardScreen({ id }: { id: string }) {
  const { data: company, isLoading } = useCompany(id)
  const { demoCompanyId } = useAuthStore()

  const isDemoCompany = id === demoCompanyId

  if (isLoading) {
    return <Spinner />
  }

  if (!company) {
    return <Paragraph>Compañía no encontrada.</Paragraph>
  }

  return (
    <YStack
      flex={1}
      space="$4"
      p="$4"
    >
      <H1>Gestionando: {company.name}</H1>

      {isDemoCompany ? (
        <UnassignedUserList companyId={id} />
      ) : (
        <Tabs
          defaultValue="users"
          orientation="horizontal"
          flex={1}
        >
          <Tabs.List>
            <Tabs.Tab value="users">
              <Paragraph>Usuarios</Paragraph>
            </Tabs.Tab>
            <Tabs.Tab value="areas">
              <Paragraph>Áreas</Paragraph>
            </Tabs.Tab>
            <Tabs.Tab value="assignments">
              <Paragraph>Asignaciones</Paragraph>
            </Tabs.Tab>
          </Tabs.List>

          <Tabs.Content
            value="users"
            pt="$4"
          >
            <UserManagementView companyId={id} />
          </Tabs.Content>
          <Tabs.Content
            value="areas"
            pt="$4"
          >
            <AreaManagementView companyId={id} />
          </Tabs.Content>
          <Tabs.Content
            value="assignments"
            pt="$4"
          >
            <AssignmentManagementView companyId={id} />
          </Tabs.Content>
        </Tabs>
      )}
    </YStack>
  )
}
