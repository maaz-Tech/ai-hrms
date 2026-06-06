import { Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import { useAuth } from './auth/AuthContext'

import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Employees from './pages/Employees'
import Attendance from './pages/Attendance'
import Payroll from './pages/Payroll'
import Performance from './pages/Performance'
import Recruitment from './pages/Recruitment'
import VoiceAgent from './pages/VoiceAgent'
import Chatbot from './pages/Chatbot'

const STAFF = ['management_admin', 'senior_manager', 'hr_recruiter']

function Protected({ children, roles }) {
  const { user } = useAuth()
  if (!user) return <Navigate to="/login" replace />
  if (roles && !roles.includes(user.role)) return <Navigate to="/" replace />
  return <Layout>{children}</Layout>
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<Protected><Dashboard /></Protected>} />
      <Route path="/employees" element={<Protected><Employees /></Protected>} />
      <Route path="/attendance" element={<Protected><Attendance /></Protected>} />
      <Route path="/payroll" element={<Protected><Payroll /></Protected>} />
      <Route path="/performance" element={<Protected><Performance /></Protected>} />
      <Route path="/recruitment" element={<Protected roles={STAFF}><Recruitment /></Protected>} />
      <Route path="/voice-agent" element={<Protected roles={STAFF}><VoiceAgent /></Protected>} />
      <Route path="/assistant" element={<Protected><Chatbot /></Protected>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
