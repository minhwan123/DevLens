import { useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import './App.css'
import { startAnalysis } from './api/client'
import { usePollJobStatus } from './hooks/usePollJobStatus'
import { LandingHero } from './components/LandingHero'
import { TerminalHeader } from './components/TerminalHeader'
import { AnalyzeForm } from './components/AnalyzeForm'
import { JobStatusPanel } from './components/JobStatusPanel'
import { ProfileHeader } from './components/ProfileHeader'
import { RadarChart } from './components/RadarChart'
import { RadarHistoryChart } from './components/RadarHistoryChart'
import { RoleFitTop3 } from './components/RoleFitTop3'
import { SkillsTable } from './components/SkillsTable'
import { StrengthsGrowthColumns } from './components/StrengthsGrowthColumns'
import { RepositoryFilterExpander } from './components/RepositoryFilterExpander'
import { ImprovementSuggestions } from './components/ImprovementSuggestions'
import { RecommendationsTabs } from './components/RecommendationsTabs'
import { RoadmapChain } from './components/RoadmapChain'
import { AiCommentary } from './components/AiCommentary'
import { PdfDownloadButton } from './components/PdfDownloadButton'

function App() {
  const [phase, setPhase] = useState<'landing' | 'app'>('landing')
  const [jobId, setJobId] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)

  const status = usePollJobStatus(jobId)

  const handleSubmit = async (username: string, careerGoal: string) => {
    setSubmitting(true)
    setSubmitError(null)
    try {
      const created = await startAnalysis(username, careerGoal)
      setJobId(created.job_id)
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : '분석 요청에 실패했습니다.')
    } finally {
      setSubmitting(false)
    }
  }

  const isPolling = jobId !== null && (!status || status.status === 'pending' || status.status === 'running')

  return (
    <AnimatePresence>
      {phase === 'landing' ? (
        <motion.div key="landing" exit={{ opacity: 0 }} transition={{ duration: 0.3 }}>
          <LandingHero onEnter={() => setPhase('app')} />
        </motion.div>
      ) : (
        <motion.div
          key="app"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.4 }}
          className="app-frame-expanded"
        >
          <div className="screen-flicker" />
          <TerminalHeader />
          <main className="app">
            {!jobId && <AnalyzeForm onSubmit={handleSubmit} disabled={submitting} error={submitError} />}

            {isPolling && <JobStatusPanel status={status?.status ?? 'pending'} />}

            {status?.status === 'failed' && (
              <div className="failed-panel">
                <p className="error-text">분석에 실패했습니다: {status.error}</p>
                <button type="button" onClick={() => setJobId(null)}>
                  다시 시도
                </button>
              </div>
            )}

            {status?.status === 'completed' && status.result && jobId && (
              <div className="result">
                <ProfileHeader profile={status.result.profile} partial={status.result.partial} />

                <section>
                  <h2>커리어 레이더</h2>
                  <RadarChart radar={status.result.radar} />
                </section>

                <section>
                  <h2>레이더 변화 추이</h2>
                  <RadarHistoryChart history={status.result.history} />
                </section>

                <section>
                  <h2>가장 잘 맞는 직군 TOP 3</h2>
                  <RoleFitTop3 roleFit={status.result.role_fit} />
                </section>

                <section>
                  <h2>스킬</h2>
                  <SkillsTable
                    skills={status.result.profile.skills}
                    repositoryEvidences={status.result.profile.repository_evidences}
                  />
                </section>

                <StrengthsGrowthColumns
                  strengths={status.result.strengths}
                  growthAreas={status.result.growth_areas}
                />

                <RepositoryFilterExpander results={status.result.filter_results} />

                <section>
                  <h2>개선 제안</h2>
                  <ImprovementSuggestions suggestions={status.result.suggestions} />
                </section>

                <section>
                  <h2>추천</h2>
                  <RecommendationsTabs recommendations={status.result.recommendations} />
                </section>

                <section>
                  <h2>학습 로드맵</h2>
                  <RoadmapChain roadmap={status.result.roadmap} />
                </section>

                <section>
                  <h2>AI 분석 의견</h2>
                  <AiCommentary commentary={status.result.ai_commentary} />
                </section>

                <PdfDownloadButton jobId={jobId} />

                <button type="button" className="restart-button" onClick={() => setJobId(null)}>
                  새로 분석하기
                </button>
              </div>
            )}
          </main>
        </motion.div>
      )}
    </AnimatePresence>
  )
}

export default App
