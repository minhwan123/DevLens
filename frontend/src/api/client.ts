import type { AnalyzeJobCreatedResponse, JobStatusResponse } from './types'

// Empty by default so requests use relative paths, handled by the Vite dev-server proxy
// (see vite.config.ts) in development. Set VITE_API_BASE_URL for a production build where
// the SPA is served from a different origin than the API (CORS_ORIGINS must allow it then).
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? ''

export async function startAnalysis(
  username: string,
  careerGoal: string,
): Promise<AnalyzeJobCreatedResponse> {
  const response = await fetch(`${API_BASE_URL}/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, career_goal: careerGoal }),
  })
  if (!response.ok) {
    throw new Error(`분석 요청에 실패했습니다 (status ${response.status})`)
  }
  return response.json()
}

export async function getStatus(jobId: string): Promise<JobStatusResponse> {
  const response = await fetch(`${API_BASE_URL}/analyze/${jobId}/status`)
  if (!response.ok) {
    throw new Error(`상태 조회에 실패했습니다 (status ${response.status})`)
  }
  return response.json()
}

export async function downloadReportPdf(jobId: string, filename: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/analyze/${jobId}/report.pdf`)
  if (!response.ok) {
    throw new Error(`PDF 다운로드에 실패했습니다 (status ${response.status})`)
  }
  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}
