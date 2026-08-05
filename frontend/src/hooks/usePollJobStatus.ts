import { useEffect, useState } from 'react'
import { getStatus } from '../api/client'
import type { JobStatusResponse } from '../api/types'

export function usePollJobStatus(jobId: string | null, intervalMs = 2000): JobStatusResponse | null {
  const [status, setStatus] = useState<JobStatusResponse | null>(null)

  useEffect(() => {
    setStatus(null)
    if (!jobId) return

    let cancelled = false
    let timer: ReturnType<typeof setTimeout>

    const tick = async () => {
      try {
        const next = await getStatus(jobId)
        if (cancelled) return
        setStatus(next)
        if (next.status === 'completed' || next.status === 'failed') return
      } catch {
        if (cancelled) return
      }
      timer = setTimeout(tick, intervalMs)
    }

    timer = setTimeout(tick, 0)
    return () => {
      cancelled = true
      clearTimeout(timer)
    }
  }, [jobId, intervalMs])

  return status
}
