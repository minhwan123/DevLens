import { useEffect, useRef } from 'react'
import type { RepositoryEvidence, SkillEvidence } from '../api/types'

function EvidenceBadge({ ok, label }: { ok: boolean; label: string }) {
  return (
    <span className={`badge ${ok ? 'badge-advanced' : 'badge-rejected'}`}>
      {ok ? '✓' : '✗'} {label}
    </span>
  )
}

export function SkillEvidenceModal({
  skill,
  repositoryEvidences,
  onClose,
}: {
  skill: SkillEvidence
  repositoryEvidences: RepositoryEvidence[]
  onClose: () => void
}) {
  const dialogRef = useRef<HTMLDialogElement>(null)

  useEffect(() => {
    dialogRef.current?.showModal()
  }, [])

  const evidenceByRepo = new Map(repositoryEvidences.map((evidence) => [evidence.repo_name, evidence]))

  return (
    <dialog
      ref={dialogRef}
      className="skill-evidence-modal"
      onClose={onClose}
      onClick={(e) => {
        if (e.target === dialogRef.current) onClose()
      }}
    >
      <div className="skill-evidence-modal-header">
        <h3 className="mono">{skill.skill}</h3>
        <span className={`badge badge-${skill.proficiency}`}>{skill.proficiency}</span>
        <button
          type="button"
          className="skill-evidence-modal-close"
          onClick={() => dialogRef.current?.close()}
          aria-label="닫기"
        >
          ✕
        </button>
      </div>

      {skill.source_repos.length === 0 ? (
        <p className="empty-state">근거가 된 저장소가 없습니다.</p>
      ) : (
        <ul className="recommendation-list">
          {skill.source_repos.map((repoName) => {
            const evidence = evidenceByRepo.get(repoName)
            return (
              <li key={repoName}>
                <div className="recommendation-name mono">{repoName}</div>
                {evidence ? (
                  <>
                    <div className="recommendation-description">
                      기술 스택: {evidence.tech_stack.join(', ') || '-'}
                    </div>
                    <div className="skill-evidence-badges">
                      <EvidenceBadge ok={evidence.has_tests} label="tests" />
                      <EvidenceBadge ok={evidence.has_ci} label="CI" />
                      <EvidenceBadge ok={evidence.has_docker} label="docker" />
                    </div>
                  </>
                ) : (
                  <p className="recommendation-description">추가 정보 없음</p>
                )}
              </li>
            )
          })}
        </ul>
      )}
    </dialog>
  )
}
