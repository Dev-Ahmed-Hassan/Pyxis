import { lazy, Suspense } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import './App.css'
import { ProtectedRoute } from './components/ProtectedRoute'
import { AuthenticatedLayout } from './layouts/AuthenticatedLayout'
import { CareerPage } from './pages/CareerPage'
import { GitHubPage } from './pages/GitHubPage'
import { InternshipsPage } from './pages/InternshipsPage'
import { InterviewsPage } from './pages/InterviewsPage'
import { LandingPage } from './pages/LandingPage'
import { LoginPage } from './pages/LoginPage'
import { ProfilePage } from './pages/ProfilePage'
import { ResumesPage } from './pages/ResumesPage'
import { SignupPage } from './pages/SignupPage'
import { WorkspacePage } from './pages/WorkspacePage'

const InternshipDetailPage = lazy(() =>
  import('./pages/InternshipDetailPage').then((module) => ({
    default: module.InternshipDetailPage,
  })),
)
const ResumeDetailPage = lazy(() =>
  import('./pages/ResumeDetailPage').then((module) => ({
    default: module.ResumeDetailPage,
  })),
)
const MatchesPage = lazy(() =>
  import('./pages/MatchesPage').then((module) => ({
    default: module.MatchesPage,
  })),
)

function DetailPageFallback() {
  return (
    <main className="app-page">
      <span className="app-page-eyebrow">Loading analysis</span>
    </main>
  )
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<AuthenticatedLayout />}>
          <Route path="/workspace" element={<WorkspacePage />} />
          <Route path="/resumes" element={<ResumesPage />} />
          <Route
            path="/resumes/:resumeId"
            element={
              <Suspense fallback={<DetailPageFallback />}>
                <ResumeDetailPage />
              </Suspense>
            }
          />
          <Route path="/internships" element={<InternshipsPage />} />
          <Route
            path="/internships/:internshipId"
            element={
              <Suspense fallback={<DetailPageFallback />}>
                <InternshipDetailPage />
              </Suspense>
            }
          />
          <Route
            path="/matches"
            element={
              <Suspense fallback={<DetailPageFallback />}>
                <MatchesPage />
              </Suspense>
            }
          />
          <Route
            path="/career"
            element={<CareerPage />}
          />
          <Route
            path="/github"
            element={<GitHubPage />}
          />
          <Route
            path="/interviews"
            element={<InterviewsPage />}
          />
          <Route
            path="/profile"
            element={<ProfilePage />}
          />
        </Route>
      </Route>
      <Route path="*" element={<Navigate replace to="/" />} />
    </Routes>
  )
}

export default App
