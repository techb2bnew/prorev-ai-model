import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import {
  DamageBadge,
  Empty,
  ErrorAlert,
  SeverityBadge,
  Spinner,
  Stat,
  StatusBadge,
  formatDateTime,
} from '../components/common.jsx'
import * as api from '../api/client.js'

const SEVERITY_COLOURS = {
  none: '#8d9ab4',
  minor: '#7dd3fc',
  moderate: '#fbbf24',
  severe: '#f43f5e',
}

export default function DashboardPage() {
  const navigate = useNavigate()
  const [stats, setStats] = useState(null)
  const [recent, setRecent] = useState(null)
  const [types, setTypes] = useState([])
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false

    Promise.all([api.getStatsSummary(), api.listInspections({ page: 1, page_size: 5 }), api.getDamageTypes()])
      .then(([summary, list, damageTypes]) => {
        if (cancelled) return
        setStats(summary)
        setRecent(list)
        setTypes(damageTypes.items)
      })
      .catch((caught) => {
        if (!cancelled) setError(caught)
      })

    return () => {
      cancelled = true
    }
  }, [])

  if (error) return <div className="page"><ErrorAlert error={error} /></div>

  if (!stats || !recent) {
    return (
      <div className="page">
        <div className="row"><Spinner /> <span className="muted">Loading dashboard…</span></div>
      </div>
    )
  }

  const totalFindings = stats.by_damage_type.reduce((sum, row) => sum + row.count, 0)
  const countsByClass = Object.fromEntries(stats.by_damage_type.map((row) => [row.class_key, row.count]))
  const worst = Object.entries(stats.by_severity).sort(
    (a, b) => ['none', 'minor', 'moderate', 'severe'].indexOf(b[0]) - ['none', 'minor', 'moderate', 'severe'].indexOf(a[0]),
  )[0]

  return (
    <div className="page">
      <div className="page-head spread">
        <div>
          <h1>Dashboard</h1>
          <p>Everything the API reports, at a glance.</p>
        </div>
        <Link className="btn btn-primary" to="/inspect">＋ New Inspection</Link>
      </div>

      <div className="grid grid-4">
        <Stat label="Inspections" value={stats.total_inspections} foot="completed analyses" />
        <Stat label="Total findings" value={totalFindings} foot="across every photo" />
        <Stat
          label="Most severe seen"
          value={worst ? worst[0] : 'none'}
          color={worst ? SEVERITY_COLOURS[worst[0]] : undefined}
          foot={worst ? `${worst[1]} finding(s)` : ''}
        />
        <Stat label="Damage classes" value={types.length} foot="detectable by the model" />
      </div>

      <div className="grid grid-2" style={{ marginTop: 14 }}>
        <div className="card">
          <div className="card-head">
            <h2>Findings by damage type</h2>
            <span className="muted small mono">GET /stats/summary</span>
          </div>

          {totalFindings === 0 ? (
            <Empty icon="◫" title="No findings yet">Run an inspection to populate this.</Empty>
          ) : (
            <div className="stack">
              {types.map((type) => {
                const count = countsByClass[type.class_key] || 0
                const share = totalFindings ? (count / totalFindings) * 100 : 0
                return (
                  <div key={type.class_key}>
                    <div className="spread" style={{ marginBottom: 4 }}>
                      <DamageBadge label={type.label} color={type.color_hex} />
                      <span className="small">
                        <strong>{count}</strong>
                        {type.is_critical && <span className="muted"> · critical</span>}
                      </span>
                    </div>
                    <div className="progress">
                      <div
                        className="progress-bar"
                        style={{ width: `${share}%`, background: type.color_hex }}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>

        <div className="card">
          <div className="card-head">
            <h2>Findings by severity</h2>
            <span className="muted small">derived by the backend, not the model</span>
          </div>

          {Object.keys(stats.by_severity).length === 0 ? (
            <Empty icon="◷" title="Nothing to show yet" />
          ) : (
            <div className="grid grid-3">
              {['minor', 'moderate', 'severe'].map((level) => (
                <Stat
                  key={level}
                  label={level}
                  value={stats.by_severity[level] || 0}
                  color={SEVERITY_COLOURS[level]}
                />
              ))}
            </div>
          )}

          <div style={{ marginTop: 16 }}>
            <h3 className="small" style={{ marginBottom: 8 }}>What the model can detect</h3>
            <div className="row" style={{ gap: 6 }}>
              {types.map((type) => (
                <DamageBadge key={type.class_key} label={type.label} color={type.color_hex} />
              ))}
            </div>
            <p className="muted small" style={{ marginTop: 8 }}>
              These six come from the model itself. Mirror damage is not among them — the supplied
              model has no mirror class.
            </p>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="card-head">
          <h2>Recent inspections</h2>
          <Link className="small" to="/history">View all →</Link>
        </div>

        {recent.items.length === 0 ? (
          <Empty icon="＋" title="No inspections yet">
            <Link to="/inspect">Upload some photos</Link> to run the first one.
          </Empty>
        ) : (
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>Customer</th>
                  <th>Status</th>
                  <th>Score</th>
                  <th>Severity</th>
                  <th>Findings</th>
                  <th>Created</th>
                </tr>
              </thead>
              <tbody>
                {recent.items.map((row) => (
                  <tr key={row.id} className="clickable" onClick={() => navigate(`/inspections/${row.id}`)}>
                    <td className="small">
                      {row.customer_name || <span className="muted">—</span>}
                      {row.vehicle_type && <span className="muted"> · {row.vehicle_type}</span>}
                    </td>
                    <td><StatusBadge status={row.status} /></td>
                    <td><strong>{row.damage_score}</strong><span className="muted small">/100</span></td>
                    <td><SeverityBadge severity={row.overall_severity} /></td>
                    <td>{row.total_detections}</td>
                    <td className="small muted">{formatDateTime(row.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
