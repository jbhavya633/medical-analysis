import { Suspense, lazy } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import { Layout } from './components/Layout'
import { LoadingScreen } from './components/ui/LoadingScreen'
import { ErrorBoundary } from './components/ui/ErrorBoundary'
import { useAuth } from './hooks/useAuth'

const Dashboard = lazy(() => import('./pages/Dashboard').then(m => ({ default: m.Dashboard })))
const PatientList = lazy(() => import('./pages/PatientList').then(m => ({ default: m.PatientList })))
const PatientDetail = lazy(() => import('./pages/PatientDetail').then(m => ({ default: m.PatientDetail })))
const ImagingViewer = lazy(() => import('./pages/ImagingViewer').then(m => ({ default: m.ImagingViewer })))
const LabAnalytics = lazy(() => import('./pages/LabAnalytics').then(m => ({ default: m.LabAnalytics })))
const ClinicalDecisionSupport = lazy(() => import('./pages/ClinicalDecisionSupport').then(m => ({ default: m.ClinicalDecisionSupport })))
const ECGAnalyzer = lazy(() => import('./pages/ECGAnalyzer').then(m => ({ default: m.ECGAnalyzer })))
const AIAssistant = lazy(() => import('./pages/AIAssistant').then(m => ({ default: m.AIAssistant })))
const QuantumLab = lazy(() => import('./pages/QuantumLab').then(m => ({ default: m.QuantumLab })))
const Settings = lazy(() => import('./pages/Settings').then(m => ({ default: m.Settings })))
const Login = lazy(() => import('./pages/Login').then(m => ({ default: m.Login })))
const NotFound = lazy(() => import('./pages/NotFound').then(m => ({ default: m.NotFound })))

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return <LoadingScreen message="Verifying authentication..." />
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return <LoadingScreen message="Checking session..." />
  }

  if (isAuthenticated) {
    return <Navigate to="/" replace />
  }

  return <>{children}</>
}

export default function App() {
  return (
    <ErrorBoundary>
      <Suspense fallback={<LoadingScreen message="Loading application..." />}>
        <Routes>
          <Route path="/login" element={
            <PublicRoute>
              <Login />
            </PublicRoute>
          } />
          <Route element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }>
            <Route path="/" element={<Dashboard />} />
            <Route path="/patients" element={<PatientList />} />
            <Route path="/patients/:id" element={<PatientDetail />} />
            <Route path="/imaging/:patientId?" element={<ImagingViewer />} />
            <Route path="/labs/:patientId?" element={<LabAnalytics />} />
            <Route path="/cds/:patientId?" element={<ClinicalDecisionSupport />} />
            <Route path="/ecg/:patientId?" element={<ECGAnalyzer />} />
            <Route path="/ai-assistant" element={<AIAssistant />} />
            <Route path="/quantum-lab" element={<QuantumLab />} />
            <Route path="/settings" element={<Settings />} />
          </Route>
          <Route path="*" element={<NotFound />} />
        </Routes>
      </Suspense>
    </ErrorBoundary>
  )
}