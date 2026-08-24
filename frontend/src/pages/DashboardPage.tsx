import { Typography } from 'antd'

export default function DashboardPage() {
  return (
    <>
      <Typography.Title level={3}>Dashboard</Typography.Title>
      <Typography.Paragraph type="secondary">
        Pay insights (headcount, USD payroll, and breakdowns) will land here
        next. Use the header badge to confirm the API is up.
      </Typography.Paragraph>
    </>
  )
}
