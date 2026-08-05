import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import { RADAR_AXIS_LABELS, type RadarSnapshot } from '../api/types'

const AXIS_COLORS: Record<string, string> = {
  programming: '#3fb950',
  project_experience: '#58a6ff',
  software_engineering: '#f0883e',
  deployment_devops: '#db61a2',
  documentation: '#a371f7',
  activity: '#e3b341',
}

function formatDate(isoString: string): string {
  const date = new Date(isoString)
  if (Number.isNaN(date.getTime())) return isoString
  return date.toLocaleDateString('ko-KR', { month: 'short', day: 'numeric' })
}

export function RadarHistoryChart({ history }: { history: RadarSnapshot[] }) {
  if (history.length < 2) {
    return <p className="empty-state">같은 GitHub 아이디로 재분석하면 변화 추이가 여기에 표시됩니다.</p>
  }

  const data = history.map((snapshot, index) => ({
    date: `${formatDate(snapshot.created_at)} #${index + 1}`,
    ...snapshot.radar,
  }))
  const axisKeys = Object.keys(RADAR_AXIS_LABELS)

  return (
    <div className="radar-history-chart">
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={data}>
          <CartesianGrid stroke="#2a2f3a" />
          <XAxis dataKey="date" tick={{ fontSize: 11, fill: '#7d8590' }} />
          <YAxis domain={[0, 100]} tick={{ fontSize: 11, fill: '#7d8590' }} />
          <Tooltip
            contentStyle={{ background: '#161b22', border: '1px solid #2a2f3a', fontSize: 12 }}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
          {axisKeys.map((key) => (
            <Line
              key={key}
              type="monotone"
              dataKey={key}
              name={RADAR_AXIS_LABELS[key]}
              stroke={AXIS_COLORS[key]}
              strokeWidth={2}
              dot={{ r: 3 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
