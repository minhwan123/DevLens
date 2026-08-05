import { useState } from 'react'
import { CAREER_GOALS } from '../api/types'

interface Props {
  onSubmit: (username: string, careerGoal: string) => void
  disabled: boolean
  error: string | null
}

export function AnalyzeForm({ onSubmit, disabled, error }: Props) {
  const [username, setUsername] = useState('')
  const [careerGoal, setCareerGoal] = useState<string>(
    CAREER_GOALS.find((goal) => goal === 'Backend') ?? CAREER_GOALS[0]
  )

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault()
    if (!username.trim()) return
    onSubmit(username.trim(), careerGoal)
  }

  return (
    <form className="analyze-form" onSubmit={handleSubmit}>
      <p className="prompt-line mono">
        <span className="prompt-caret">$</span> analyze --github &lt;username&gt; --goal &lt;role&gt;
      </p>

      <label htmlFor="username">GitHub 사용자명</label>
      <input
        id="username"
        value={username}
        onChange={(event) => setUsername(event.target.value)}
        placeholder="octocat"
        disabled={disabled}
        required
      />

      <label htmlFor="career_goal">목표 직무</label>
      <select
        id="career_goal"
        value={careerGoal}
        onChange={(event) => setCareerGoal(event.target.value)}
        disabled={disabled}
      >
        {CAREER_GOALS.map((goal) => (
          <option key={goal} value={goal}>
            {goal}
          </option>
        ))}
      </select>

      <button type="submit" disabled={disabled}>
        {disabled ? '분석 중...' : '분석 시작'}
      </button>

      {error && <p className="error-text">{error}</p>}
    </form>
  )
}
