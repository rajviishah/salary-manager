import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { AutoComplete, Form, Input, Modal, Select, message } from 'antd'
import {
  apiErrorMessage,
  createEmployee,
  fetchLookups,
  formFieldsFromApiError,
} from '../api.ts'
import { autoCompleteOptions, lookupOptions } from '../formOptions.ts'

type CreateFormValues = {
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
  amount: string
  currency: string
  effective_date: string
}

type Props = {
  open: boolean
  onClose: () => void
  onCreated: (id: number) => void
}

export default function EmployeeCreateModal({ open, onClose, onCreated }: Props) {
  const [form] = Form.useForm<CreateFormValues>()
  const queryClient = useQueryClient()

  const lookups = useQuery({
    queryKey: ['lookups'],
    queryFn: fetchLookups,
    enabled: open,
  })

  const create = useMutation({
    mutationFn: createEmployee,
    onSuccess: async (employee) => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['employees'] }),
        queryClient.invalidateQueries({ queryKey: ['lookups'] }),
      ])
      message.success('Employee added')
      form.resetFields()
      onCreated(employee.id)
    },
    onError: (error) => {
      const fields = formFieldsFromApiError(error).map((field) =>
        field.name[0] === 'salary'
          ? { ...field, name: field.name.slice(1) }
          : field,
      )
      if (fields.length) {
        form.setFields(fields as Parameters<typeof form.setFields>[0])
      }
      message.error(apiErrorMessage(error))
    },
  })

  return (
    <Modal
      title="Add employee"
      open={open}
      onCancel={() => {
        if (create.isPending) return
        onClose()
      }}
      onOk={() => form.submit()}
      okText="Add employee"
      confirmLoading={create.isPending}
      okButtonProps={{ disabled: create.isPending }}
      destroyOnClose
      width={640}
    >
      <Form<CreateFormValues>
        form={form}
        layout="vertical"
        initialValues={{ status: 'active' }}
        onFinish={(values) => {
          create.mutate({
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
            salary: {
              amount: String(values.amount).trim(),
              currency: values.currency,
              effective_date: values.effective_date,
            },
          })
        }}
      >
        <Form.Item
          name="employee_number"
          label="Employee number"
          rules={[{ required: true, message: 'Employee number is required' }]}
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
          <AutoComplete options={autoCompleteOptions(lookups.data?.countries)} />
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
          <AutoComplete options={autoCompleteOptions(lookups.data?.job_levels)} />
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
          <Select options={lookupOptions(lookups.data?.statuses)} />
        </Form.Item>
        <Form.Item
          name="amount"
          label="Starting salary"
          rules={[{ required: true, message: 'Amount is required' }]}
        >
          <Input placeholder="75000.00" />
        </Form.Item>
        <Form.Item
          name="currency"
          label="Currency"
          rules={[{ required: true, message: 'Currency is required' }]}
        >
          <Select options={lookupOptions(lookups.data?.currencies)} />
        </Form.Item>
        <Form.Item
          name="effective_date"
          label="Salary effective date"
          rules={[{ required: true, message: 'Effective date is required' }]}
        >
          <Input type="date" />
        </Form.Item>
      </Form>
    </Modal>
  )
}
