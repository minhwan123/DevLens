const BAR_LENGTH = 20

export function PriorityBar({ score }: { score: number }) {
  const clamped = Math.min(1, Math.max(0, score))
  const filled = Math.round(clamped * BAR_LENGTH)
  const bar = '█'.repeat(filled) + '░'.repeat(BAR_LENGTH - filled)

  return (
    <div className="priority-bar mono">
      <span className="priority-bar-track">{bar}</span>
      <span className="priority-bar-pct">{Math.round(clamped * 100)}%</span>
    </div>
  )
}
