import { OctocatScene } from './OctocatScene'

export function LandingHero({ onEnter }: { onEnter: () => void }) {
  return (
    <div className="landing-hero">
      <OctocatScene onEnter={onEnter} />
      <p className="hero-caption mono">노트북을 클릭해서 시작하세요</p>
    </div>
  )
}
