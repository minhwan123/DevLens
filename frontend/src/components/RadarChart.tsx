import {
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart as RechartsRadarChart,
  ResponsiveContainer,
} from 'recharts'
import { RADAR_AXIS_LABELS, type CareerRadarProfile } from '../api/types'

export function RadarChart({ radar }: { radar: CareerRadarProfile }) {
  const data = (Object.keys(RADAR_AXIS_LABELS) as (keyof CareerRadarProfile)[]).map((key) => ({
    axis: RADAR_AXIS_LABELS[key],
    score: radar[key],
  }))

  return (
    <div className="radar-chart">
      <ResponsiveContainer width="100%" height={320}>
        <RechartsRadarChart data={data} outerRadius="75%">
          <PolarGrid stroke="#2a2f3a" />
          <PolarAngleAxis dataKey="axis" tick={{ fontSize: 12, fill: '#7d8590' }} />
          <PolarRadiusAxis domain={[0, 100]} tick={false} axisLine={false} />
          <Radar dataKey="score" stroke="#3fb950" fill="#3fb950" fillOpacity={0.35} />
        </RechartsRadarChart>
      </ResponsiveContainer>
      <table className="score-table">
        <tbody>
          {data.map((row) => (
            <tr key={row.axis}>
              <td>{row.axis}</td>
              <td>{row.score.toFixed(0)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
