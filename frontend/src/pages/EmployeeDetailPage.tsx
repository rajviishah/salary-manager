import { useQuery } from '@tanstack/react-query'
import { Alert, Button, Descriptions, Spin, Typography } from 'antd'
import { Link, useParams } from 'react-router-dom'
import { fetchEmployee, formatSalary } from '../api.ts'

export default function EmployeeDetailPage() {
  const { id } = useParams()
  const employeeId = Number(id)
  const validId = Number.isInteger(employeeId) && employeeId > 0

  const query = useQuery({
    queryKey: ['employee', employeeId],
    queryFn: () => fetchEmployee(employeeId),
    enabled: validId,
  })

  return (
    <>
      <Link to="/employees">
        <Button type="link" style={{ paddingInline: 0, marginBottom: 8 }}>
          ← Back to directory
        </Button>
      </Link>
      <Typography.Title level={3}>Employee</Typography.Title>

      {!validId && (
        <Alert type="error" showIcon message="Invalid employee id" />
      )}

      {validId && query.isLoading && <Spin />}

      {validId && query.isError && (
        <Alert
          type="error"
          showIcon
          message="Could not load this employee"
          description="The record may not exist, or the API on port 8000 is down."
        />
      )}

      {query.data && (
        <Descriptions bordered column={1} size="small">
          <Descriptions.Item label="Name">
            {query.data.last_name}, {query.data.first_name}
          </Descriptions.Item>
          <Descriptions.Item label="Employee number">
            {query.data.employee_number}
          </Descriptions.Item>
          <Descriptions.Item label="Email">{query.data.email}</Descriptions.Item>
          <Descriptions.Item label="Country">{query.data.country}</Descriptions.Item>
          <Descriptions.Item label="Department">
            {query.data.department}
          </Descriptions.Item>
          <Descriptions.Item label="Job title">
            {query.data.job_title}
          </Descriptions.Item>
          <Descriptions.Item label="Job level">
            {query.data.job_level}
          </Descriptions.Item>
          <Descriptions.Item label="Hire date">
            {query.data.hire_date}
          </Descriptions.Item>
          <Descriptions.Item label="Status">{query.data.status}</Descriptions.Item>
          <Descriptions.Item label="Salary">
            {formatSalary(query.data.salary)}
          </Descriptions.Item>
          <Descriptions.Item label="Salary effective">
            {query.data.salary?.effective_date ?? '—'}
          </Descriptions.Item>
        </Descriptions>
      )}
    </>
  )
}
