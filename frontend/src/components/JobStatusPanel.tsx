import type { JobStatus } from '../api/types'

const STATUS_LABELS: Record<JobStatus, string> = {
  pending: '분석 대기 중...',
  running: 'GitHub 저장소를 분석하는 중입니다...',
  completed: '분석 완료',
  failed: '분석 실패',
}

export function JobStatusPanel({ status }: { status: JobStatus }) {
  return (
    <div className="job-status-panel">
      <div className={`spinner ${status === 'completed' || status === 'failed' ? 'spinner--done' : ''}`} />
      <p>{STATUS_LABELS[status]}</p>
    </div>
  )
}
