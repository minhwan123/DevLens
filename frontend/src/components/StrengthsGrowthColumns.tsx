export function StrengthsGrowthColumns({
  strengths,
  growthAreas,
}: {
  strengths: string[]
  growthAreas: string[]
}) {
  return (
    <div className="strengths-growth-columns">
      <div className="column">
        <h3>강점</h3>
        <ul>{strengths.length ? strengths.map((s) => <li key={s}>{s}</li>) : <li>(none identified)</li>}</ul>
      </div>
      <div className="column">
        <h3>성장 영역</h3>
        <ul>
          {growthAreas.length ? growthAreas.map((g) => <li key={g}>{g}</li>) : <li>(none)</li>}
        </ul>
      </div>
    </div>
  )
}
