import { useState } from 'react'
import type { RepositoryEvidence, SkillEvidence } from '../api/types'
import { SkillEvidenceModal } from './SkillEvidenceModal'

export function SkillsTable({
  skills,
  repositoryEvidences,
}: {
  skills: SkillEvidence[]
  repositoryEvidences: RepositoryEvidence[]
}) {
  const [selectedSkill, setSelectedSkill] = useState<SkillEvidence | null>(null)

  if (skills.length === 0) {
    return <p className="empty-state">감지된 스킬이 없습니다.</p>
  }

  return (
    <>
      <table className="skills-table">
        <thead>
          <tr>
            <th>스킬</th>
            <th>숙련도</th>
            <th>근거 레포</th>
          </tr>
        </thead>
        <tbody>
          {skills.map((skill) => (
            <tr key={skill.skill}>
              <td>
                <button
                  type="button"
                  className="skill-name-button mono"
                  onClick={() => setSelectedSkill(skill)}
                >
                  {skill.skill}
                </button>
              </td>
              <td>
                <span className={`badge badge-${skill.proficiency}`}>{skill.proficiency}</span>
              </td>
              <td>{skill.source_repos.join(', ') || '-'}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {selectedSkill && (
        <SkillEvidenceModal
          skill={selectedSkill}
          repositoryEvidences={repositoryEvidences}
          onClose={() => setSelectedSkill(null)}
        />
      )}
    </>
  )
}
