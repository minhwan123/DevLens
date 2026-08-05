import type { RoleFit } from '../api/types'
import { PriorityBar } from './PriorityBar'

export function RoleFitTop3({ roleFit }: { roleFit: RoleFit[] }) {
  if (roleFit.length === 0) {
    return <p className="empty-state">역할 적합도를 계산할 수 없습니다.</p>
  }

  return (
    <ul className="recommendation-list">
      {roleFit.map((fit) => (
        <li key={fit.role}>
          <div className="recommendation-name">{fit.role}</div>
          <PriorityBar score={fit.fit_score} />
          {fit.matched_skills.length > 0 && (
            <div className="recommendation-description">보유: {fit.matched_skills.join(', ')}</div>
          )}
          {fit.missing_skills.length > 0 && (
            <div className="recommendation-description">부족: {fit.missing_skills.join(', ')}</div>
          )}
        </li>
      ))}
    </ul>
  )
}
