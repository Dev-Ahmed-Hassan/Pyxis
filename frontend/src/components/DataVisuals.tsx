import {
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from 'recharts'
import './DataVisuals.css'

export type DonutDatum = {
  name: string
  value: number
  color: string
}

export function DataDonut({
  data,
  label,
  total,
}: {
  data: DonutDatum[]
  label: string
  total: number
}) {
  const visibleData = data.filter((item) => item.value > 0)

  return (
    <div className="data-donut">
      <div className="data-donut-chart">
        <ResponsiveContainer height="100%" width="100%">
          <PieChart>
            <Pie
              data={visibleData}
              dataKey="value"
              innerRadius={51}
              outerRadius={70}
              paddingAngle={2}
              stroke="none"
            >
              {visibleData.map((item) => (
                <Cell fill={item.color} key={item.name} />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                border: '1px solid #c2c8c5',
                borderRadius: 0,
                boxShadow: 'none',
                fontSize: 11,
              }}
            />
          </PieChart>
        </ResponsiveContainer>
        <div className="data-donut-center">
          <strong>{total}</strong>
          <span>{label}</span>
        </div>
      </div>
      <div className="data-donut-legend">
        {data.map((item) => (
          <div key={item.name}>
            <i style={{ background: item.color }} />
            <span>{item.name}</span>
            <strong>{item.value}</strong>
          </div>
        ))}
      </div>
    </div>
  )
}

export function ConfidenceBar({
  confidence,
  compact = false,
}: {
  confidence: number
  compact?: boolean
}) {
  const percentage = Math.round(confidence * 100)

  return (
    <div className={`confidence-bar ${compact ? 'is-compact' : ''}`}>
      <div>
        <span>Extraction confidence</span>
        <strong>{percentage}%</strong>
      </div>
      <i>
        <span style={{ width: `${percentage}%` }} />
      </i>
    </div>
  )
}

export function EvidenceDisclosure({
  confidence,
  evidence,
  source,
}: {
  confidence: number
  evidence: string | null
  source?: string
}) {
  return (
    <details className="evidence-disclosure">
      <summary>
        <span>Inspect evidence</span>
        <strong>{Math.round(confidence * 100)}%</strong>
      </summary>
      <ConfidenceBar confidence={confidence} compact />
      <dl>
        {source && (
          <div>
            <dt>Source</dt>
            <dd>{source}</dd>
          </div>
        )}
        <div>
          <dt>Excerpt</dt>
          <dd>{evidence || 'No source excerpt was stored.'}</dd>
        </div>
      </dl>
    </details>
  )
}
