import type { RepositoryFilterResult } from '../api/types'

export function RepositoryFilterExpander({ results }: { results: RepositoryFilterResult[] }) {
  return (
    <details className="repository-filter-expander">
      <summary>레포지토리 필터링 결과 ({results.length}개)</summary>
      <table>
        <thead>
          <tr>
            <th>레포지토리</th>
            <th>채택 여부</th>
            <th>사유</th>
          </tr>
        </thead>
        <tbody>
          {results.map((result) => (
            <tr key={result.repo_name}>
              <td className="mono">{result.repo_name}</td>
              <td>
                <span className={`badge ${result.accepted ? 'badge-advanced' : 'badge-rejected'}`}>
                  {result.accepted ? '✓ accepted' : '✗ rejected'}
                </span>
              </td>
              <td>{result.reason}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </details>
  )
}
