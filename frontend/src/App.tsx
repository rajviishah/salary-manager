import { Layout, Menu, Tag, Typography } from 'antd'
import { useQuery } from '@tanstack/react-query'
import { Link, Navigate, Route, Routes, useLocation } from 'react-router-dom'
import { fetchHealth } from './api.ts'
import DashboardPage from './pages/DashboardPage.tsx'
import EmployeesPage from './pages/EmployeesPage.tsx'

const { Header, Content } = Layout

export default function App() {
  const location = useLocation()
  const health = useQuery({ queryKey: ['health'], queryFn: fetchHealth })
  const selectedKey = location.pathname.startsWith('/employees')
    ? '/employees'
    : '/'

  let apiTag = <Tag>API …</Tag>
  if (health.isSuccess && health.data.status === 'ok') {
    apiTag = <Tag color="success">API ok</Tag>
  } else if (health.isError) {
    apiTag = <Tag color="error">API down</Tag>
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 24,
          paddingInline: 24,
        }}
      >
        <Typography.Text strong style={{ color: '#fff', whiteSpace: 'nowrap' }}>
          ACME Salary Manager
        </Typography.Text>
        <Menu
          theme="dark"
          mode="horizontal"
          selectedKeys={[selectedKey]}
          style={{ flex: 1, minWidth: 0 }}
          items={[
            { key: '/', label: <Link to="/">Dashboard</Link> },
            { key: '/employees', label: <Link to="/employees">Employees</Link> },
          ]}
        />
        {apiTag}
      </Header>
      <Content style={{ padding: 24, background: '#f5f5f5' }}>
        <div
          style={{
            maxWidth: 960,
            margin: '0 auto',
            background: '#fff',
            padding: 24,
            borderRadius: 8,
          }}
        >
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/employees" element={<EmployeesPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </div>
      </Content>
    </Layout>
  )
}
