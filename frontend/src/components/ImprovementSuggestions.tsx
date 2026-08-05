import { RADAR_AXIS_LABELS, type ImprovementSuggestion } from '../api/types'

export function ImprovementSuggestions({ suggestions }: { suggestions: ImprovementSuggestion[] }) {
  if (suggestions.length === 0) {
    return <p className="empty-state">추가로 제안할 개선 사항이 없습니다.</p>
  }

  const byRepo = new Map<string, ImprovementSuggestion[]>()
  for (const suggestion of suggestions) {
    const group = byRepo.get(suggestion.repo_name) ?? []
    group.push(suggestion)
    byRepo.set(suggestion.repo_name, group)
  }

  return (
    <ul className="recommendation-list">
      {[...byRepo.entries()].map(([repoName, repoSuggestions]) => (
        <li key={repoName}>
          <div className="recommendation-name mono">{repoName}</div>
          <ul className="suggestion-sublist">
            {repoSuggestions.map((suggestion) => (
              <li key={`${suggestion.repo_name}-${suggestion.axis}-${suggestion.message}`}>
                <span className="badge badge-intermediate">
                  {RADAR_AXIS_LABELS[suggestion.axis] ?? suggestion.axis}
                </span>{' '}
                {suggestion.message}
              </li>
            ))}
          </ul>
        </li>
      ))}
    </ul>
  )
}
