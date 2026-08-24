export type HealthResponse = {
  status: string
}

export type EmployeePreview = {
  id: number
  first_name: string
  last_name: string
  employee_number: string
}

export type EmployeeListResponse = {
  items: EmployeePreview[]
  total: number
  page: number
  page_size: number
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

export function fetchEmployeesPreview(): Promise<EmployeeListResponse> {
  return getJson<EmployeeListResponse>('/api/employees?page=1&page_size=5')
}
