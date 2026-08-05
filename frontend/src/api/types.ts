export type JobStatus = 'pending' | 'running' | 'completed' | 'failed'

export type ProficiencyLevel = 'beginner' | 'intermediate' | 'advanced'

export interface SkillEvidence {
  skill: string
  proficiency: ProficiencyLevel
  source_repos: string[]
}

export interface RepositoryEvidence {
  repo_name: string
  tech_stack: string[]
  has_tests: boolean
  has_ci: boolean
  has_docker: boolean
  commit_frequency: number
  quality_score: number
  readme_quality_score: number
  domain_tags: string[]
}

export interface DeveloperProfile {
  schema_version: string
  skills: SkillEvidence[]
  domains: string[]
  career_goal: string
  project_level: ProficiencyLevel
  repository_evidences: RepositoryEvidence[]
}

export interface CareerRadarProfile {
  programming: number
  project_experience: number
  software_engineering: number
  deployment_devops: number
  documentation: number
  activity: number
}

export const RADAR_AXIS_LABELS: Record<string, string> = {
  programming: 'Programming',
  project_experience: 'Project Experience',
  software_engineering: 'Software Engineering',
  deployment_devops: 'Deployment & DevOps',
  documentation: 'Documentation',
  activity: 'Activity',
}

export interface RepositoryFilterResult {
  repo_name: string
  accepted: boolean
  score: number
  reason: string
}

export type RecommendationCategory = 'skill' | 'project' | 'dataset'

export interface RecommendationItem {
  item_id: string
  name: string
  category: RecommendationCategory
  tags: string[]
  description: string
}

export interface Recommendation {
  item: RecommendationItem
  priority_score: number
  skill_gap_weight: number
  similarity: number
  career_goal_relevance: number
}

export interface ImprovementSuggestion {
  repo_name: string
  axis: string
  message: string
}

export interface RoleFit {
  role: string
  fit_score: number
  matched_skills: string[]
  missing_skills: string[]
}

export interface RadarSnapshot {
  created_at: string
  career_goal: string
  radar: CareerRadarProfile
}

export interface JobResultResponse {
  profile: DeveloperProfile
  filter_results: RepositoryFilterResult[]
  partial: boolean
  radar: CareerRadarProfile
  recommendations: Recommendation[]
  suggestions: ImprovementSuggestion[]
  role_fit: RoleFit[]
  history: RadarSnapshot[]
  roadmap: string[]
  strengths: string[]
  growth_areas: string[]
  ai_commentary: string
}

export interface JobStatusResponse {
  job_id: string
  status: JobStatus
  result: JobResultResponse | null
  error: string | null
}

export interface AnalyzeJobCreatedResponse {
  job_id: string
  status: JobStatus
}

export const CAREER_GOALS = [
  'AI Engineer',
  'Data Scientist',
  'Data Analyst',
  'Data Engineer',
  'Backend',
  'Frontend',
  'DevOps',
  'Mobile Developer',
  'Full-stack Developer',
] as const
