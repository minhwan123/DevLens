import { useState } from 'react'
import type { Recommendation, RecommendationCategory } from '../api/types'
import { PriorityBar } from './PriorityBar'

const TABS: { category: RecommendationCategory; label: string }[] = [
  { category: 'skill', label: '기술' },
  { category: 'project', label: '프로젝트' },
  { category: 'dataset', label: '데이터셋' },
]

export function RecommendationsTabs({ recommendations }: { recommendations: Recommendation[] }) {
  const [active, setActive] = useState<RecommendationCategory>('skill')
  const items = recommendations.filter((rec) => rec.item.category === active).slice(0, 5)

  return (
    <div className="recommendations-tabs">
      <div className="tab-buttons">
        {TABS.map((tab) => (
          <button
            key={tab.category}
            className={tab.category === active ? 'active' : ''}
            onClick={() => setActive(tab.category)}
            type="button"
          >
            {tab.label}
          </button>
        ))}
      </div>
      {items.length === 0 ? (
        <p className="empty-state">추천 항목이 없습니다.</p>
      ) : (
        <ul className="recommendation-list">
          {items.map((rec) => (
            <li key={rec.item.item_id}>
              <div className="recommendation-name">{rec.item.name}</div>
              <div className="recommendation-description">{rec.item.description}</div>
              <PriorityBar score={rec.priority_score} />
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
