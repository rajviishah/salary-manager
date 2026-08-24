import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { Alert, Button, Input, Select, Space, Table, Typography } from 'antd'
import type { TableProps } from 'antd'
import type { SorterResult } from 'antd/es/table/interface'
import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { fetchEmployees, fetchLookups, formatSalary } from '../api.ts'
import type { Employee } from '../api.ts'
import { lookupOptions } from '../formOptions.ts'
import EmployeeCreateModal from './EmployeeCreateModal.tsx'

const PAGE_SIZE = 25
const DEFAULT_SORT = 'last_name'
const SORT_FIELDS = ['last_name', 'employee_number', 'hire_date', 'amount'] as const

function useDebouncedValue<T>(value: T, delayMs: number): T {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const timer = window.setTimeout(() => setDebounced(value), delayMs)
    return () => window.clearTimeout(timer)
  }, [value, delayMs])
  return debounced
}

function parsePage(raw: string | null): number {
  const n = Number(raw ?? '1')
  if (!Number.isInteger(n) || n < 1) return 1
  return n
}

function sortOrderFor(
  sort: string,
  field: string,
): 'ascend' | 'descend' | undefined {
  if (sort === field) return 'ascend'
  if (sort === `-${field}`) return 'descend'
  return undefined
}

function apiSortFromTable(
  sorter: SorterResult<Employee> | SorterResult<Employee>[],
): string {
  const single = Array.isArray(sorter) ? sorter[0] : sorter
  const raw = single?.columnKey ?? single?.field
  const field = Array.isArray(raw)
    ? String(raw[raw.length - 1] ?? DEFAULT_SORT)
    : String(raw ?? DEFAULT_SORT)
  const key = (SORT_FIELDS as readonly string[]).includes(field)
    ? field
    : DEFAULT_SORT
  if (single?.order === 'descend') return `-${key}`
  if (single?.order === 'ascend') return key
  return DEFAULT_SORT
}

export default function EmployeesPage() {
  const navigate = useNavigate()
  const [searchParams, setSearchParams] = useSearchParams()
  const [createOpen, setCreateOpen] = useState(false)

  const qFromUrl = searchParams.get('q') ?? ''
  const country = searchParams.get('country') ?? undefined
  const department = searchParams.get('department') ?? undefined
  const jobLevel = searchParams.get('job_level') ?? undefined
  const status = searchParams.get('status') ?? undefined
  const page = parsePage(searchParams.get('page'))
  const sort = searchParams.get('sort') ?? DEFAULT_SORT

  const [searchInput, setSearchInput] = useState(qFromUrl)
  const debouncedQ = useDebouncedValue(searchInput, 300)
  const q = debouncedQ.trim()

  useEffect(() => {
    const nextQ = debouncedQ.trim()
    if (nextQ === qFromUrl) return
    setSearchParams(
      (prev) => {
        const next = new URLSearchParams(prev)
        if (nextQ) next.set('q', nextQ)
        else next.delete('q')
        next.delete('page')
        return next
      },
      { replace: true },
    )
  }, [debouncedQ, qFromUrl, setSearchParams])

  const listParams = useMemo(
    () => ({
      q: q || undefined,
      country,
      department,
      job_level: jobLevel,
      status,
      page,
      page_size: PAGE_SIZE,
      sort,
    }),
    [q, country, department, jobLevel, status, page, sort],
  )

  const lookups = useQuery({
    queryKey: ['lookups'],
    queryFn: fetchLookups,
  })

  const list = useQuery({
    queryKey: ['employees', listParams],
    queryFn: () => fetchEmployees(listParams),
    placeholderData: keepPreviousData,
  })

  function patchParams(
    updates: Record<string, string | undefined>,
    options?: { resetPage?: boolean },
  ) {
    setSearchParams((prev) => {
      const next = new URLSearchParams(prev)
      for (const [key, value] of Object.entries(updates)) {
        if (value) next.set(key, value)
        else next.delete(key)
      }
      if (options?.resetPage !== false) next.delete('page')
      return next
    })
  }

  const columns: TableProps<Employee>['columns'] = [
    {
      title: 'Name',
      key: 'last_name',
      dataIndex: 'last_name',
      sorter: true,
      sortOrder: sortOrderFor(sort, 'last_name'),
      render: (_value, row) => `${row.last_name}, ${row.first_name}`,
    },
    {
      title: 'Employee no.',
      dataIndex: 'employee_number',
      key: 'employee_number',
      sorter: true,
      sortOrder: sortOrderFor(sort, 'employee_number'),
    },
    {
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
      ellipsis: true,
    },
    {
      title: 'Country',
      dataIndex: 'country',
      key: 'country',
    },
    {
      title: 'Department',
      dataIndex: 'department',
      key: 'department',
    },
    {
      title: 'Level',
      dataIndex: 'job_level',
      key: 'job_level',
    },
    {
      title: 'Hire date',
      dataIndex: 'hire_date',
      key: 'hire_date',
      sorter: true,
      sortOrder: sortOrderFor(sort, 'hire_date'),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 100,
    },
    {
      title: 'Salary',
      key: 'amount',
      sorter: true,
      sortOrder: sortOrderFor(sort, 'amount'),
      render: (_value, row) => formatSalary(row.salary),
    },
    {
      title: '',
      key: 'view',
      width: 72,
      render: (_value, row) => (
        <Button
          type="link"
          onClick={(event) => {
            event.stopPropagation()
            navigate(`/employees/${row.id}`)
          }}
        >
          View
        </Button>
      ),
    },
  ]

  const onTableChange: TableProps<Employee>['onChange'] = (
    pagination,
    _filters,
    sorter,
  ) => {
    const nextSort = apiSortFromTable(sorter)
    const nextPage = pagination.current ?? 1
    patchParams(
      {
        sort: nextSort === DEFAULT_SORT ? undefined : nextSort,
        page: nextPage > 1 ? String(nextPage) : undefined,
      },
      { resetPage: false },
    )
  }

  return (
    <>
      <Space
        align="start"
        style={{ width: '100%', justifyContent: 'space-between' }}
      >
        <div>
          <Typography.Title level={3} style={{ marginBottom: 8 }}>
            Employees
          </Typography.Title>
          <Typography.Paragraph type="secondary">
            Search and filter the directory. Open a row to edit profile and
            current salary, or add an employee who is not in the seed data.
          </Typography.Paragraph>
        </div>
        <Button type="primary" onClick={() => setCreateOpen(true)}>
          Add employee
        </Button>
      </Space>

      <EmployeeCreateModal
        open={createOpen}
        onClose={() => setCreateOpen(false)}
        onCreated={(employeeId) => {
          setCreateOpen(false)
          navigate(`/employees/${employeeId}`)
        }}
      />

      <Space wrap style={{ marginBottom: 16 }} size="middle">
        <Input.Search
          allowClear
          placeholder="Name, email, or employee number"
          value={searchInput}
          onChange={(event) => setSearchInput(event.target.value)}
          onSearch={(value) => setSearchInput(value)}
          style={{ width: 320 }}
        />
        <Select
          allowClear
          placeholder="Country"
          value={country}
          options={lookupOptions(lookups.data?.countries)}
          onChange={(value) => patchParams({ country: value })}
          style={{ width: 180 }}
        />
        <Select
          allowClear
          placeholder="Department"
          value={department}
          options={lookupOptions(lookups.data?.departments)}
          onChange={(value) => patchParams({ department: value })}
          style={{ width: 180 }}
        />
        <Select
          allowClear
          placeholder="Job level"
          value={jobLevel}
          options={lookupOptions(lookups.data?.job_levels)}
          onChange={(value) => patchParams({ job_level: value })}
          style={{ width: 140 }}
        />
        <Select
          allowClear
          placeholder="Status"
          value={status}
          options={lookupOptions(lookups.data?.statuses)}
          onChange={(value) => patchParams({ status: value })}
          style={{ width: 140 }}
        />
      </Space>

      {lookups.isError && (
        <Alert
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
          message="Filter options could not be loaded"
          description="You can still search the directory. Start the API on port 8000 if it is down."
        />
      )}

      {list.isError && (
        <Alert
          type="error"
          showIcon
          style={{ marginBottom: 16 }}
          message="Could not load employees"
          description="Start the FastAPI server on http://127.0.0.1:8000, then refresh."
        />
      )}

      <Table<Employee>
        rowKey="id"
        columns={columns}
        dataSource={list.data?.items ?? []}
        loading={list.isLoading || list.isFetching}
        onChange={onTableChange}
        onRow={(row) => ({
          onClick: () => navigate(`/employees/${row.id}`),
          style: { cursor: 'pointer' },
        })}
        locale={{ emptyText: list.isError ? ' ' : 'No employees match these filters' }}
        pagination={{
          current: page,
          pageSize: PAGE_SIZE,
          total: list.data?.total ?? 0,
          showSizeChanger: false,
          showTotal: (total) => `${total.toLocaleString()} employees`,
        }}
        scroll={{ x: 1100 }}
      />
    </>
  )
}
