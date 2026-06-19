import { Toaster } from 'react-hot-toast'
import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { AppLayout } from './components/layout/AppLayout'
import { ATSPage } from './pages/ATSPage'
import { CareerPage } from './pages/CareerPage'
import { ChatPage } from './pages/ChatPage'
import { DashboardPage } from './pages/DashboardPage'
import { InterviewPage } from './pages/InterviewPage'
import { JobsPage } from './pages/JobsPage'
import { SettingsPage } from './pages/SettingsPage'
import { SkillGapPage } from './pages/SkillGapPage'
import { UploadPage } from './pages/UploadPage'
import { ResumeProvider } from './store/resumeStore'

export default function App() {
  return (
    <ResumeProvider>
      <BrowserRouter>
        <Routes>
          <Route element={<AppLayout />}>
            <Route index element={<UploadPage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/ats" element={<ATSPage />} />
            <Route path="/skill-gap" element={<SkillGapPage />} />
            <Route path="/interview" element={<InterviewPage />} />
            <Route path="/career" element={<CareerPage />} />
            <Route path="/jobs" element={<JobsPage />} />
            <Route path="/chat" element={<ChatPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Route>
        </Routes>
      </BrowserRouter>

      <Toaster
        position="bottom-right"
        toastOptions={{
          style: {
            background: '#1f2937',
            color: '#f3f4f6',
            border: '1px solid #374151',
            borderRadius: '0.75rem',
          },
          success: { iconTheme: { primary: '#22c55e', secondary: '#fff' } },
          error: { iconTheme: { primary: '#ef4444', secondary: '#fff' } },
        }}
      />
    </ResumeProvider>
  )
}
