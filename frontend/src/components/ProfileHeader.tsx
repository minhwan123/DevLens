import type { DeveloperProfile } from '../api/types'

export function ProfileHeader({ profile, partial }: { profile: DeveloperProfile; partial: boolean }) {
  return (
    <section className="profile-header">
      {partial && (
        <p className="warning-text">
          ⚠ GitHub API 요청 한도로 인해 일부 저장소만 분석된 부분(partial) 결과입니다.
        </p>
      )}
      <div className="profile-metrics">
        <div className="metric">
          <span className="metric-label">목표 직무</span>
          <span className="metric-value">{profile.career_goal}</span>
        </div>
        <div className="metric">
          <span className="metric-label">프로젝트 레벨</span>
          <span className="metric-value">{profile.project_level}</span>
        </div>
        <div className="metric">
          <span className="metric-label">분석된 레포</span>
          <span className="metric-value">{profile.repository_evidences.length}</span>
        </div>
      </div>
      <p className="domains">도메인: {profile.domains.length ? profile.domains.join(', ') : '-'}</p>
    </section>
  )
}
