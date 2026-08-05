export function RoadmapChain({ roadmap }: { roadmap: string[] }) {
  if (roadmap.length === 0) {
    return <p className="empty-state">(none)</p>
  }

  return (
    <div className="roadmap-chain">
      {roadmap.map((step, index) => (
        <span key={step}>
          <span className="roadmap-step">{step}</span>
          {index < roadmap.length - 1 && <span className="roadmap-arrow"> → </span>}
        </span>
      ))}
    </div>
  )
}
