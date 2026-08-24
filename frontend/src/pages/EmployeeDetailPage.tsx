import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Alert,
  AutoComplete,
  Button,
  Card,
  Col,
  Empty,
  Form,
  Input,
  Row,
  Select,
  Space,
  Spin,
  Typography,
  message,
} from 'antd'
import { useEffect } from 'react'
import { Link, useParams } from 'react-router-dom'
import {
  ApiError,
  apiErrorMessage,
  fetchEmployee,
  fetchLookups,
  formFieldsFromApiError,
  updateEmployee,
  updateEmployeeSalary,
} from '../api.ts'
import type { Employee, EmployeeUpdatePayload, SalaryWrite } from '../api.ts'
import {
  autoCompleteOptions,
  lookupOptionsWithCurrent,
} from '../formOptions.ts'

type ProfileFormValues = {
  employee_number: string
  first_name: string
  last_name: string
  email: string
  country: string
  department: string
  job_title: string
  job_level: string
  hire_date: string
  status: string
}

type SalaryFormValues = {
  amount: string
  currency: string
  effective_date: string
}

function profileValues(employee: Employee): ProfileFormValues {
  return {
    employee_number: employee.employee_number,
    first_name: employee.first_name,
    last_name: employee.last_name,
    email: employee.email,
    country: employee.country,
    department: employee.department,
    job_title: employee.job_title,
    job_level: employee.job_level,
    hire_date: employee.hire_date,
    status: employee.status,
  }
}

function salaryValues(employee: Employee): SalaryFormValues | null {
  if (!employee.salary) return null
  return {
    amount: employee.salary.amount,
    currency: employee.salary.currency,
    effective_date: employee.salary.effective_date,
  }
}

function isNotFound(error: unknown): boolean {
  return error instanceof ApiError && error.status === 404
}

export default function EmployeeDetailPage() {
  const { id } = useParams()
  const employeeId = Number(id)
  const validId = Number.isInteger(employeeId) && employeeId > 0
  const queryClient = useQueryClient()
  const [profileForm] = Form.useForm<ProfileFormValues>()
  const [salaryForm] = Form.useForm<SalaryFormValues>()

  const query = useQuery({
    queryKey: ['employee', employeeId],
    queryFn: () => fetchEmployee(employeeId),
    enabled: validId,
  })

  const lookups = useQuery({
    queryKey: ['lookups'],
    queryFn: fetchLookups,
    enabled: validId && Boolean(query.data),
  })

  useEffect(() => {
    if (!query.data) return
    profileForm.setFieldsValue(profileValues(query.data))
    const salary = salaryValues(query.data)
    if (salary) salaryForm.setFieldsValue(salary)
  }, [query.data, profileForm, salaryForm])

  const saveProfile = useMutation({
    mutationFn: (payload: EmployeeUpdatePayload) =>
      updateEmployee(employeeId, payload),
    onSuccess: async (employee) => {
      queryClient.setQueryData(['employee', employeeId], employee)
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['employee', employeeId] }),
        queryClient.invalidateQueries({ queryKey: ['employees'] }),
        queryClient.invalidateQueries({ queryKey: ['lookups'] }),
      ])
      message.success('Profile saved')
    },
    onError: (error) => {
      const fields = formFieldsFromApiError(error)
      if (fields.length) {
        profileForm.setFields(fields as Parameters<typeof profileForm.setFields>[0])
      }
      message.error(apiErrorMessage(error))
    },
  })

  const saveSalary = useMutation({
    mutationFn: (payload: SalaryWrite) =>
      updateEmployeeSalary(employeeId, payload),
    onSuccess: async (employee) => {
      queryClient.setQueryData(['employee', employeeId], employee)
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['employee', employeeId] }),
        queryClient.invalidateQueries({ queryKey: ['employees'] }),
      ])
      message.success('Salary updated')
    },
    onError: (error) => {
      const fields = formFieldsFromApiError(error)
      if (fields.length) {
        salaryForm.setFields(fields as Parameters<typeof salaryForm.setFields>[0])
      }
      message.error(apiErrorMessage(error))
    },
  })

  return (
    <>
      <Link to="/employees">
        <Button type="link" style={{ paddingInline: 0, marginBottom: 8 }}>
          ← Back to directory
        </Button>
      </Link>
      <Typography.Title level={3}>
        {query.data
          ? `${query.data.last_name}, ${query.data.first_name}`
          : 'Employee'}
      </Typography.Title>

      {!validId && (
        <Alert type="error" showIcon message="Invalid employee id" />
      )}

      {validId && query.isLoading && <Spin />}

      {validId && query.isError && isNotFound(query.error) && (
        <Empty description="This employee was not found" />
      )}

      {validId && query.isError && !isNotFound(query.error) && (
        <Alert
          type="error"
          showIcon
          message="Could not load this employee"
          description="The API on port 8000 may be down."
        />
      )}

      {query.data && (
        <Row gutter={[16, 16]}>
          <Col xs={24} lg={14}>
            <Card title="Profile">
              <Form<ProfileFormValues>
                form={profileForm}
                layout="vertical"
                onFinish={(values) => {
                  saveProfile.mutate({
                    employee_number: values.employee_number.trim(),
                    first_name: values.first_name.trim(),
                    last_name: values.last_name.trim(),
                    email: values.email.trim(),
                    country: values.country.trim(),
                    department: values.department.trim(),
                    job_title: values.job_title.trim(),
                    job_level: values.job_level.trim(),
                    hire_date: values.hire_date,
                    status: values.status,
                  })
                }}
              >
                <Form.Item
                  name="employee_number"
                  label="Employee number"
                  rules={[
                    { required: true, message: 'Employee number is required' },
                  ]}
                >
                  <Input maxLength={32} />
                </Form.Item>
                <Form.Item
                  name="first_name"
                  label="First name"
                  rules={[{ required: true, message: 'First name is required' }]}
                >
                  <Input maxLength={100} />
                </Form.Item>
                <Form.Item
                  name="last_name"
                  label="Last name"
                  rules={[{ required: true, message: 'Last name is required' }]}
                >
                  <Input maxLength={100} />
                </Form.Item>
                <Form.Item
                  name="email"
                  label="Email"
                  rules={[{ required: true, message: 'Email is required' }]}
                >
                  <Input maxLength={255} />
                </Form.Item>
                <Form.Item
                  name="country"
                  label="Country"
                  rules={[{ required: true, message: 'Country is required' }]}
                >
                  <AutoComplete
                    options={autoCompleteOptions(lookups.data?.countries)}
                  />
                </Form.Item>
                <Form.Item
                  name="department"
                  label="Department"
                  rules={[{ required: true, message: 'Department is required' }]}
                >
                  <AutoComplete
                    options={autoCompleteOptions(lookups.data?.departments)}
                  />
                </Form.Item>
                <Form.Item
                  name="job_title"
                  label="Job title"
                  rules={[{ required: true, message: 'Job title is required' }]}
                >
                  <Input maxLength={150} />
                </Form.Item>
                <Form.Item
                  name="job_level"
                  label="Job level"
                  rules={[{ required: true, message: 'Job level is required' }]}
                >
                  <AutoComplete
                    options={autoCompleteOptions(lookups.data?.job_levels)}
                  />
                </Form.Item>
                <Form.Item
                  name="hire_date"
                  label="Hire date"
                  rules={[{ required: true, message: 'Hire date is required' }]}
                >
                  <Input type="date" />
                </Form.Item>
                <Form.Item
                  name="status"
                  label="Status"
                  rules={[{ required: true, message: 'Status is required' }]}
                >
                  <Select
                    options={lookupOptionsWithCurrent(
                      lookups.data?.statuses,
                      query.data.status,
                    )}
                  />
                </Form.Item>
                <Form.Item>
                  <Button
                    type="primary"
                    htmlType="submit"
                    loading={saveProfile.isPending}
                    disabled={saveProfile.isPending}
                  >
                    Save profile
                  </Button>
                </Form.Item>
              </Form>
            </Card>
          </Col>
          <Col xs={24} lg={10}>
            <Card title="Current salary">
              {!query.data.salary && (
                <Alert
                  type="info"
                  showIcon
                  message="No current salary on this record"
                />
              )}
              {query.data.salary && (
                <Form<SalaryFormValues>
                  form={salaryForm}
                  layout="vertical"
                  onFinish={(values) => {
                    saveSalary.mutate({
                      amount: String(values.amount).trim(),
                      currency: values.currency,
                      effective_date: values.effective_date,
                    })
                  }}
                >
                  <Form.Item
                    name="amount"
                    label="Amount"
                    extra="Sent as a decimal string (for example 75000.00)."
                    rules={[{ required: true, message: 'Amount is required' }]}
                  >
                    <Input />
                  </Form.Item>
                  <Form.Item
                    name="currency"
                    label="Currency"
                    rules={[
                      { required: true, message: 'Currency is required' },
                    ]}
                  >
                    <Select
                      options={lookupOptionsWithCurrent(
                        lookups.data?.currencies,
                        query.data.salary.currency,
                      )}
                    />
                  </Form.Item>
                  <Form.Item
                    name="effective_date"
                    label="Effective date"
                    rules={[
                      {
                        required: true,
                        message: 'Effective date is required',
                      },
                    ]}
                  >
                    <Input type="date" />
                  </Form.Item>
                  <Form.Item>
                    <Space>
                      <Button
                        type="primary"
                        htmlType="submit"
                        loading={saveSalary.isPending}
                        disabled={saveSalary.isPending}
                      >
                        Update salary
                      </Button>
                    </Space>
                  </Form.Item>
                </Form>
              )}
            </Card>
          </Col>
        </Row>
      )}
    </>
  )
}
