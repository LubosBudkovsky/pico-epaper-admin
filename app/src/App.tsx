
import { Navigate, Route, Routes } from 'react-router-dom'
import Layout from './components/layout/Layout'
import Home from './routes/Home'
import EpaperSettings from './routes/epaper/settings/EpaperSettings'
import ContextProviders from './routes/epaper/context/ContextProviders'
import Login from './routes/auth/Login'
import AuthSettings from './routes/auth/AuthSettings'
import RequireAuth from './modules/RequireAuth'
import { useAuth } from './modules/AuthProvider'
import NetworkSettings from './routes/network/NetworkSettings'

export default function App() {
  const auth = useAuth()
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <RequireAuth state={auth.state}>
            <Layout />
          </RequireAuth>
        }
      >
        <Route path="/" element={<Home />} />
        <Route path="/network/settings" element={<NetworkSettings />} />
        <Route path="/epaper/settings" element={<EpaperSettings />} />
        <Route path="/epaper/context" element={<ContextProviders />} />
        <Route path="/auth/settings" element={<AuthSettings />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}
