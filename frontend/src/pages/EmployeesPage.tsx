import { Alert, List, Spin, Typography } from 'antd'
import { useQuery } from '@tanstack/react-query'
import { fetchEmployeesPreview } from '../api.ts'

export default function EmployeesPage() {
  const query = useQuery({
    queryKey: ['employees-preview'],
    queryFn: fetchEmployeesPreview,
  })

  return (
    <>
      <Typography.Title level={3}>Employees</Typography.Title>
      <Typography.Paragraph type="secondary">
        Full directory with search and filters is next. This preview only
        proves the 10k-employee API is reachable.
      </Typography.Paragraph>
      {query.isLoading && <Spin />}
      {query.isError && (
        <Alert
          type="error"
          showIcon
          message="Could not load employees"
          description="Start the FastAPI server on http://127.0.0.1:8000, then refresh."
        />
      )}
      {query.data && (
        <>
          <Typography.Paragraph>
            Showing {query.data.items.length} of {query.data.total.toLocaleString()}{' '}
            employees.
          </Typography.Paragraph>
          <List
            bordered
            dataSource={query.data.items}
            renderItem={(item) => (
              <List.Item>
                {item.last_name}, {item.first_name} ({item.employee_number})
              </List.Item>
            )}
          />
        </>
      )}
    </>
  )
}
