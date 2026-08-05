import { useState } from 'react'
import { downloadReportPdf } from '../api/client'

export function PdfDownloadButton({ jobId }: { jobId: string }) {
  const [state, setState] = useState<'idle' | 'downloading' | 'error'>('idle')

  const handleClick = async () => {
    setState('downloading')
    try {
      await downloadReportPdf(jobId, `devlens-report-${jobId}.pdf`)
      setState('idle')
    } catch {
      setState('error')
    }
  }

  return (
    <div className="pdf-download">
      <button type="button" onClick={handleClick} disabled={state === 'downloading'}>
        {state === 'downloading' ? '다운로드 중...' : 'PDF 리포트 다운로드'}
      </button>
      {state === 'error' && <p className="error-text">PDF 다운로드에 실패했습니다. 다시 시도해주세요.</p>}
    </div>
  )
}
