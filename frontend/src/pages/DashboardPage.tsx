import { useQuery } from '@tanstack/react-query'
import {
  Alert,
  Card,
  Col,
  Row,
  Segmented,
  Space,
  Spin,
  Statistic,
  Table,
  Typography,
} from 'antd'
import type { ColumnsType } from 'antd/es/table'
import { useMemo, useState } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import {
  apiErrorMessage,
  fetchAnalyticsByCountry,
  fetchAnalyticsByDepartment,
  fetchAnalyticsByLevel,
  fetchAnalyticsSummary,
  formatAmount,
  formatCompactUsd,
  formatUsd,
  parseDecimal,
} from '../api.ts'
import type {
  AnalyticsByCountry,
  AnalyticsByDepartment,
  AnalyticsByLevel,
  AnalyticsStatus,
  CurrencyMixItem,
} from '../api.ts'

const CHART_COLORS = [
  '#1677ff',
  '#13c2c2',
  '#52c41a',
  '#faad14',
  '#eb2f96',
  '#722ed1',
  '#fa541c',
  '#2f54eb',
]

type ChartRow = {
  name: string
  headcount: number
  avgUsd: number
  totalUsd: number
}

function toChartRows(
  rows: { name: string; headcount: number; avg_usd: string; total_usd: string }[],
): ChartRow[] {
  return rows.map((row) => ({
    name: row.name,
    headcount: row.headcount,
    avgUsd: parseDecimal(row.avg_usd) ?? 0,
    totalUsd: parseDecimal(row.total_usd) ?? 0,
  }))
}

function usdColumn<T>(
  title: string,
  dataIndex: keyof T & string,
): ColumnsType<T>[number] {
  return {
    title,
    dataIndex,
    key: dataIndex,
    align: 'right',
    render: (value: string) => formatUsd(value),
    sorter: (a, b) =>
      (parseDecimal(String(a[dataIndex])) ?? 0) -
      (parseDecimal(String(b[dataIndex])) ?? 0),
  }
}

function headcountColumn<T extends { headcount: number }>(): ColumnsType<T>[number] {
  return {
    title: 'Headcount',
    dataIndex: 'headcount',
    key: 'headcount',
    align: 'right',
    render: (value: number) => value.toLocaleString('en-US'),
    sorter: (a, b) => a.headcount - b.headcount,
  }
}

function chartTooltipUsd(value: unknown, name: unknown) {
  const n = typeof value === 'number' ? value : Number(value)
  const label = typeof name === 'string' ? name : String(name ?? '')
  const formatted = Number.isFinite(n) ? formatUsd(n.toFixed(2)) : '—'
  return [formatted, label === 'avgUsd' ? 'Avg USD' : 'Total USD']
}

export default function DashboardPage() {
  const [status, setStatus] = useState<AnalyticsStatus>('active')

  const summary = useQuery({
    queryKey: ['analytics', 'summary', status],
    queryFn: () => fetchAnalyticsSummary(status),
  })
  const byCountry = useQuery({
    queryKey: ['analytics', 'by-country', status],
    queryFn: () => fetchAnalyticsByCountry(status),
  })
  const byDepartment = useQuery({
    queryKey: ['analytics', 'by-department', status],
    queryFn: () => fetchAnalyticsByDepartment(status),
  })
  const byLevel = useQuery({
    queryKey: ['analytics', 'by-level', status],
    queryFn: () => fetchAnalyticsByLevel(status),
  })

  const countryChart = useMemo(
    () =>
      toChartRows(
        (byCountry.data ?? []).map((row) => ({
          name: row.country,
          headcount: row.headcount,
          avg_usd: row.avg_usd,
          total_usd: row.total_usd,
        })),
      ),
    [byCountry.data],
  )
  const departmentChart = useMemo(
    () =>
      toChartRows(
        (byDepartment.data ?? []).map((row) => ({
          name: row.department,
          headcount: row.headcount,
          avg_usd: row.avg_usd,
          total_usd: row.total_usd,
        })),
      ),
    [byDepartment.data],
  )
  const levelChart = useMemo(
    () =>
      toChartRows(
        (byLevel.data ?? []).map((row) => ({
          name: row.job_level,
          headcount: row.headcount,
          avg_usd: row.avg_usd,
          total_usd: row.total_usd,
        })),
      ),
    [byLevel.data],
  )
  const mixChart = useMemo(
    () =>
      (summary.data?.currency_mix ?? []).map((row) => ({
        name: row.currency,
        value: row.headcount,
      })),
    [summary.data],
  )

  const firstLoad =
    summary.isPending ||
    byCountry.isPending ||
    byDepartment.isPending ||
    byLevel.isPending

  const errors = [
    summary.isError ? `Summary: ${apiErrorMessage(summary.error)}` : null,
    byCountry.isError ? `By country: ${apiErrorMessage(byCountry.error)}` : null,
    byDepartment.isError
      ? `By department: ${apiErrorMessage(byDepartment.error)}`
      : null,
    byLevel.isError ? `By level: ${apiErrorMessage(byLevel.error)}` : null,
  ].filter((part): part is string => Boolean(part))

  const countryColumns: ColumnsType<AnalyticsByCountry> = [
    { title: 'Country', dataIndex: 'country', key: 'country' },
    headcountColumn<AnalyticsByCountry>(),
    usdColumn<AnalyticsByCountry>('Avg USD', 'avg_usd'),
    usdColumn<AnalyticsByCountry>('Median USD', 'median_usd'),
    usdColumn<AnalyticsByCountry>('Total USD', 'total_usd'),
  ]

  const departmentColumns: ColumnsType<AnalyticsByDepartment> = [
    { title: 'Department', dataIndex: 'department', key: 'department' },
    headcountColumn<AnalyticsByDepartment>(),
    usdColumn<AnalyticsByDepartment>('Avg USD', 'avg_usd'),
    usdColumn<AnalyticsByDepartment>('Median USD', 'median_usd'),
    usdColumn<AnalyticsByDepartment>('Total USD', 'total_usd'),
  ]

  const levelColumns: ColumnsType<AnalyticsByLevel> = [
    { title: 'Job level', dataIndex: 'job_level', key: 'job_level' },
    headcountColumn<AnalyticsByLevel>(),
    usdColumn<AnalyticsByLevel>('Avg USD', 'avg_usd'),
    usdColumn<AnalyticsByLevel>('Median USD', 'median_usd'),
    usdColumn<AnalyticsByLevel>('Total USD', 'total_usd'),
  ]

  const mixColumns: ColumnsType<CurrencyMixItem> = [
    { title: 'Currency', dataIndex: 'currency', key: 'currency' },
    headcountColumn<CurrencyMixItem>(),
    {
      title: 'Total (local)',
      dataIndex: 'total_local',
      key: 'total_local',
      align: 'right',
      render: (value: string) => formatAmount(value),
      sorter: (a, b) =>
        (parseDecimal(a.total_local) ?? 0) - (parseDecimal(b.total_local) ?? 0),
    },
  ]

  return (
    <>
      <Space
        align="start"
        style={{ width: '100%', justifyContent: 'space-between' }}
      >
        <div>
          <Typography.Title level={3} style={{ marginBottom: 8 }}>
            How the org pays people
          </Typography.Title>
          <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
            USD-normalized payroll for {status} employees. Local amounts are
            converted with the FX table (amount × usd_rate).
          </Typography.Paragraph>
        </div>
        <Segmented
          value={status}
          onChange={(value) => setStatus(value as AnalyticsStatus)}
          options={[
            { label: 'Active', value: 'active' },
            { label: 'Inactive', value: 'inactive' },
          ]}
        />
      </Space>

      {errors.length > 0 && (
        <Alert
          type="error"
          showIcon
          style={{ marginTop: 16 }}
          message="Could not load pay insights"
          description={
            <>
              {errors.join(' ')} Start the FastAPI server on
              http://127.0.0.1:8000, then refresh.
            </>
          }
        />
      )}

      <Spin spinning={firstLoad}>
        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          <Col xs={24} sm={12} lg={8} xl={4}>
            <Card>
              <Statistic
                title="Headcount"
                value={summary.data?.headcount ?? 0}
                groupSeparator=","
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={8} xl={5}>
            <Card>
              <Statistic
                title="Total USD payroll"
                prefix="$"
                value={parseDecimal(summary.data?.total_usd ?? '') ?? 0}
                precision={2}
                groupSeparator=","
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={8} xl={5}>
            <Card>
              <Statistic
                title="Avg USD"
                prefix="$"
                value={parseDecimal(summary.data?.avg_usd ?? '') ?? 0}
                precision={2}
                groupSeparator=","
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={8} xl={5}>
            <Card>
              <Statistic
                title="Median USD"
                prefix="$"
                value={parseDecimal(summary.data?.median_usd ?? '') ?? 0}
                precision={2}
                groupSeparator=","
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={8} xl={5}>
            <Card>
              <Statistic
                title="p90 USD"
                prefix="$"
                value={parseDecimal(summary.data?.p90_usd ?? '') ?? 0}
                precision={2}
                groupSeparator=","
              />
            </Card>
          </Col>
        </Row>

        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          <Col xs={24} lg={10}>
            <Card title="Currency mix">
              <div style={{ width: '100%', height: 280 }}>
                <ResponsiveContainer>
                  <PieChart>
                    <Pie
                      data={mixChart}
                      dataKey="value"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      innerRadius={48}
                      outerRadius={88}
                      paddingAngle={2}
                    >
                      {mixChart.map((entry, index) => (
                        <Cell
                          key={entry.name}
                          fill={CHART_COLORS[index % CHART_COLORS.length]}
                        />
                      ))}
                    </Pie>
                    <Tooltip
                      formatter={(value) => [
                        typeof value === 'number'
                          ? value.toLocaleString('en-US')
                          : String(value),
                        'Headcount',
                      ]}
                    />
                    <Legend />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <Table<CurrencyMixItem>
                size="small"
                rowKey="currency"
                columns={mixColumns}
                dataSource={summary.data?.currency_mix ?? []}
                pagination={false}
                locale={{ emptyText: summary.isError ? ' ' : 'No currency data' }}
              />
            </Card>
          </Col>
          <Col xs={24} lg={14}>
            <Card title="Average USD by country">
              <Typography.Paragraph type="secondary">
                India vs US (and other markets) on the same USD scale.
              </Typography.Paragraph>
              <div style={{ width: '100%', height: 320 }}>
                <ResponsiveContainer>
                  <BarChart data={countryChart} margin={{ left: 8, right: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" interval={0} angle={-20} textAnchor="end" height={60} />
                    <YAxis tickFormatter={formatCompactUsd} />
                    <Tooltip formatter={chartTooltipUsd} />
                    <Bar dataKey="avgUsd" name="Avg USD" fill="#1677ff" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <Table<AnalyticsByCountry>
                size="small"
                rowKey="country"
                columns={countryColumns}
                dataSource={byCountry.data ?? []}
                pagination={false}
                scroll={{ x: 640 }}
                locale={{ emptyText: byCountry.isError ? ' ' : 'No country data' }}
              />
            </Card>
          </Col>
        </Row>

        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          <Col xs={24} lg={12}>
            <Card title="By department">
              <div style={{ width: '100%', height: 280 }}>
                <ResponsiveContainer>
                  <BarChart data={departmentChart} margin={{ left: 8, right: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" interval={0} angle={-20} textAnchor="end" height={70} />
                    <YAxis tickFormatter={formatCompactUsd} />
                    <Tooltip formatter={chartTooltipUsd} />
                    <Bar dataKey="totalUsd" name="Total USD" fill="#13c2c2" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <Table<AnalyticsByDepartment>
                size="small"
                rowKey="department"
                columns={departmentColumns}
                dataSource={byDepartment.data ?? []}
                pagination={false}
                scroll={{ x: 640 }}
                locale={{
                  emptyText: byDepartment.isError ? ' ' : 'No department data',
                }}
              />
            </Card>
          </Col>
          <Col xs={24} lg={12}>
            <Card title="By job level">
              <div style={{ width: '100%', height: 280 }}>
                <ResponsiveContainer>
                  <BarChart data={levelChart} margin={{ left: 8, right: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis tickFormatter={formatCompactUsd} />
                    <Tooltip formatter={chartTooltipUsd} />
                    <Bar dataKey="avgUsd" name="Avg USD" fill="#722ed1" />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <Table<AnalyticsByLevel>
                size="small"
                rowKey="job_level"
                columns={levelColumns}
                dataSource={byLevel.data ?? []}
                pagination={false}
                scroll={{ x: 640 }}
                locale={{ emptyText: byLevel.isError ? ' ' : 'No level data' }}
              />
            </Card>
          </Col>
        </Row>
      </Spin>
    </>
  )
}
