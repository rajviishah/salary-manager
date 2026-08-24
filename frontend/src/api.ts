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

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(path)
  if (!response.ok) {
    throw new Error(`${path} failed (${response.status})`)
  }
  return response.json() as Promise<T>
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

export function formatSalary(salary: Salary | null): string {
  if (!salary) return '—'
  return `${salary.amount} ${salary.currency}`
}
