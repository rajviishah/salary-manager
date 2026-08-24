export type HealthResponse = {
  status: string
}

export type Salary = {
  id: number
  employee_id: number
  amount: string
  currency: string
  effective_date: string
  created_at: string | null
  updated_at: string | null
}

export type Employee = {
  id: number
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
  created_at: string | null
  updated_at: string | null
  salary: Salary | null
}

export type EmployeeListResponse = {
  items: Employee[]
  total: number
  page: number
  page_size: number
}

export type Lookups = {
  countries: string[]
  departments: string[]
  job_levels: string[]
  statuses: string[]
  currencies: string[]
}

export type EmployeeListParams = {
  q?: string
  country?: string
  department?: string
  job_level?: string
  status?: string
  page?: number
  page_size?: number
  sort?: string
}

export type SalaryWrite = {
  amount: string
  currency: string
  effective_date: string
}

export type EmployeeUpdatePayload = {
  employee_number?: string
  first_name?: string
  last_name?: string
  email?: string
  country?: string
  department?: string
  job_title?: string
  job_level?: string
  hire_date?: string
  status?: string
}

export type EmployeeCreatePayload = {
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
  salary: SalaryWrite
}

export type AnalyticsStatus = 'active' | 'inactive'

export type CurrencyMixItem = {
  currency: string
  headcount: number
  total_local: string
}

export type AnalyticsSummary = {
  headcount: number
  total_usd: string
  avg_usd: string
  median_usd: string
  p90_usd: string
  min_usd: string
  max_usd: string
  currency_mix: CurrencyMixItem[]
}

export type AnalyticsBreakdownRow = {
  headcount: number
  total_usd: string
  avg_usd: string
  median_usd: string
}

export type AnalyticsByCountry = AnalyticsBreakdownRow & {
  country: string
}

export type AnalyticsByDepartment = AnalyticsBreakdownRow & {
  department: string
}

export type AnalyticsByLevel = AnalyticsBreakdownRow & {
  job_level: string
}

export type FormFieldError = {
  name: (string | number)[]
  errors: string[]
}

export class ApiError extends Error {
  status: number
  detail: unknown

  constructor(status: number, detail: unknown, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null
}

async function readBody(response: Response): Promise<unknown> {
  const text = await response.text()
  if (!text) return null
  try {
    return JSON.parse(text) as unknown
  } catch {
    return text
  }
}

function detailFromBody(body: unknown): unknown {
  if (isRecord(body) && 'detail' in body) return body.detail
  return body
}

async function parseResponse<T>(response: Response, path: string): Promise<T> {
  const body = await readBody(response)
  if (!response.ok) {
    throw new ApiError(
      response.status,
      detailFromBody(body),
      `${path} failed (${response.status})`,
    )
  }
  return body as T
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(path)
  return parseResponse<T>(response, path)
}

async function sendJson<T>(
  path: string,
  method: 'POST' | 'PATCH',
  payload: unknown,
): Promise<T> {
  const response = await fetch(path, {
    method,
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify(payload),
  })
  return parseResponse<T>(response, path)
}

function issueMessage(item: unknown): string | null {
  if (!isRecord(item) || typeof item.msg !== 'string') return null
  return item.msg
}

function issuePath(item: unknown): (string | number)[] {
  if (!isRecord(item) || !Array.isArray(item.loc)) return []
  return item.loc.filter((part) => part !== 'body') as (string | number)[]
}

export function apiErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (typeof error.detail === 'string') return error.detail
    if (Array.isArray(error.detail)) {
      const parts = error.detail
        .map((item) => {
          const msg = issueMessage(item)
          if (!msg) return null
          const path = issuePath(item).join('.')
          return path ? `${path}: ${msg}` : msg
        })
        .filter((part): part is string => Boolean(part))
      if (parts.length) return parts.join('; ')
    }
    return error.message
  }
  if (error instanceof Error) return error.message
  return 'Request failed'
}

export function formFieldsFromApiError(error: unknown): FormFieldError[] {
  if (!(error instanceof ApiError)) return []

  if (typeof error.detail === 'string') {
    const text = error.detail
    const lower = text.toLowerCase()
    if (lower.includes('email')) {
      return [{ name: ['email'], errors: [text] }]
    }
    if (lower.includes('employee number')) {
      return [{ name: ['employee_number'], errors: [text] }]
    }
    if (lower.includes('currency')) {
      return [{ name: ['currency'], errors: [text] }]
    }
    return []
  }

  if (!Array.isArray(error.detail)) return []

  return error.detail.flatMap((item) => {
    const msg = issueMessage(item)
    const name = issuePath(item)
    if (!msg || name.length === 0) return []
    return [{ name, errors: [msg] }]
  })
}

export function fetchHealth(): Promise<HealthResponse> {
  return getJson<HealthResponse>('/health')
}

export function fetchLookups(): Promise<Lookups> {
  return getJson<Lookups>('/api/lookups')
}

export function fetchEmployee(id: number): Promise<Employee> {
  return getJson<Employee>(`/api/employees/${id}`)
}

export function fetchEmployees(
  params: EmployeeListParams,
): Promise<EmployeeListResponse> {
  const search = new URLSearchParams()
  if (params.q) search.set('q', params.q)
  if (params.country) search.set('country', params.country)
  if (params.department) search.set('department', params.department)
  if (params.job_level) search.set('job_level', params.job_level)
  if (params.status) search.set('status', params.status)
  search.set('page', String(params.page ?? 1))
  search.set('page_size', String(params.page_size ?? 25))
  if (params.sort) search.set('sort', params.sort)
  return getJson<EmployeeListResponse>(`/api/employees?${search.toString()}`)
}

export function createEmployee(
  payload: EmployeeCreatePayload,
): Promise<Employee> {
  return sendJson<Employee>('/api/employees', 'POST', payload)
}

export function updateEmployee(
  id: number,
  payload: EmployeeUpdatePayload,
): Promise<Employee> {
  return sendJson<Employee>(`/api/employees/${id}`, 'PATCH', payload)
}

export function updateEmployeeSalary(
  id: number,
  payload: SalaryWrite,
): Promise<Employee> {
  return sendJson<Employee>(`/api/employees/${id}/salary`, 'PATCH', payload)
}

export function formatSalary(salary: Salary | null): string {
  if (!salary) return '—'
  return `${salary.amount} ${salary.currency}`
}

/** Parse API Decimal JSON strings without treating leftover junk as a number. */
export function parseDecimal(value: string): number | null {
  if (typeof value !== 'string') return null
  const trimmed = value.trim()
  if (!trimmed) return null
  if (!/^-?\d+(\.\d+)?$/.test(trimmed)) return null
  const n = Number(trimmed)
  return Number.isFinite(n) ? n : null
}

export function formatUsd(value: string): string {
  const n = parseDecimal(value)
  if (n === null) return '—'
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(n)
}

export function formatAmount(value: string): string {
  const n = parseDecimal(value)
  if (n === null) return '—'
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(n)
}

export function formatCompactUsd(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    notation: 'compact',
    maximumFractionDigits: 1,
  }).format(value)
}

function analyticsPath(path: string, status: AnalyticsStatus): string {
  const search = new URLSearchParams({ status })
  return `${path}?${search.toString()}`
}

export function fetchAnalyticsSummary(
  status: AnalyticsStatus = 'active',
): Promise<AnalyticsSummary> {
  return getJson<AnalyticsSummary>(analyticsPath('/api/analytics/summary', status))
}

export function fetchAnalyticsByCountry(
  status: AnalyticsStatus = 'active',
): Promise<AnalyticsByCountry[]> {
  return getJson<AnalyticsByCountry[]>(
    analyticsPath('/api/analytics/by-country', status),
  )
}

export function fetchAnalyticsByDepartment(
  status: AnalyticsStatus = 'active',
): Promise<AnalyticsByDepartment[]> {
  return getJson<AnalyticsByDepartment[]>(
    analyticsPath('/api/analytics/by-department', status),
  )
}

export function fetchAnalyticsByLevel(
  status: AnalyticsStatus = 'active',
): Promise<AnalyticsByLevel[]> {
  return getJson<AnalyticsByLevel[]>(
    analyticsPath('/api/analytics/by-level', status),
  )
}
