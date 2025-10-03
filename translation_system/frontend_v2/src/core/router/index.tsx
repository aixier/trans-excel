import { Routes, Route } from 'react-router-dom'
import { lazy, Suspense } from 'react'
import { Spin } from 'antd'

// Lazy load pages
const HomePage = lazy(() => import('@pages/HomePage'))
const UploadPage = lazy(() => import('@pages/UploadPage'))
const AnalysisPage = lazy(() => import('@pages/AnalysisPage'))
const TranslationPage = lazy(() => import('@pages/TranslationPage'))
const MonitorPage = lazy(() => import('@pages/MonitorPage'))
const ExportPage = lazy(() => import('@pages/ExportPage'))

const Loading = () => (
  <div className="flex items-center justify-center h-screen">
    <Spin size="large" />
  </div>
)

const Router = () => {
  return (
    <Suspense fallback={<Loading />}>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/upload" element={<UploadPage />} />
        <Route path="/analysis/:sessionId" element={<AnalysisPage />} />
        <Route path="/translation/:sessionId" element={<TranslationPage />} />
        <Route path="/monitor/:sessionId" element={<MonitorPage />} />
        <Route path="/export/:sessionId" element={<ExportPage />} />
      </Routes>
    </Suspense>
  )
}

export default Router