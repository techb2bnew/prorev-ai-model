import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  DamageBadge,
  Empty,
  ErrorAlert,
  SeverityBadge,
  Spinner,
  StatusBadge,
  formatDateTime,
} from '../components/common.jsx'
import * as api from '../api/client.js'

const STATUSES = ['', 'queued', 'processing', 'completed', 'partial_success', 'failed']

export default function HistoryPage() {
  const navigate = useNavigate()

  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [filters, setFilters] = useState({ status: '', damage_type: '', date_from: '', date_to: '' })
  const [result, setResult] = useState(null)
  const [types, setTypes] = useState([])
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.getDamageTypes().then((data) => setTypes(data.items)).catch(() => {})
  }, [])

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setError(null)

    api
      .listInspections({ page, page_size: pageSize, ...filters })
      .then((data) => {
        if (!cancelled) setResult(data)
      })
      .catch((caught) => {
        if (!cancelled) setError(caught)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [page, pageSize, filters])

  function updateFilter(key, value) {
    setPage(1)
    setFilters((current) => ({ ...current, [key]: value }))
  }

  const colours = Object.fromEntries(types.map((type) => [type.class_key, type.color_hex]))

  return (
    <div className="page">
      <div className="page-head">
        <h1>History</h1>
        <p>Every inspection is kept permanently. Filter by status, damage type or date.</p>
      </div>

      <div className="card">
        <div className="field-row">
          <div className="field">
            <label>Status</label>
            <select value={filters.status} onChange={(event) => updateFilter('status', event.target.value)}>
              {STATUSES.map((value) => (
                <option key={value} value={value}>{value === '' ? 'Any status' : value.replace('_', ' ')}</option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>Damage type</label>
            <select
              value={filters.damage_type}
              onChange={(event) => updateFilter('damage_type', event.target.value)}
            >
              <option value="">Any damage</option>
              {types.map((type) => (
                <option key={type.class_key} value={type.class_key}>{type.label}</option>
              ))}
            </select>
          </div>
          <div className="field">
            <label>From</label>
            <input
              type="date"
              value={filters.date_from}
              onChange={(event) => updateFilter('date_from', event.target.value)}
            />
          </div>
          <div className="field">
            <label>To</label>
            <input
              type="date"
              value={filters.date_to}
              onChange={(event) => updateFilter('date_to', event.target.value)}
            />
          </div>
          <div className="field">
            <label>Per page</label>
            <select
              value={pageSize}
              onChange={(event) => {
                setPage(1)
                setPageSize(Number(event.target.value))
              }}
            >
              {[5, 10, 20, 50].map((size) => (
                <option key={size} value={size}>{size}</option>
              ))}
            </select>
          </div>
        </div>
      </div>

      <ErrorAlert error={error} />

      <div className="card">
        <div className="card-head">
          <h2>Inspections</h2>
          {result && <span className="muted small">{result.total} total</span>}
        </div>

        {loading && (
          <div className="row" style={{ padding: '14px 0' }}>
            <Spinner /> <span className="muted">Loading…</span>
          </div>
        )}

        {!loading && result?.items.length === 0 && (
          <Empty icon="⏱" title="Nothing here yet">
            {Object.values(filters).some(Boolean)
              ? 'No inspections match these filters.'
              : 'Run your first inspection to see it appear here.'}
          </Empty>
        )}

        {!loading && result?.items.length > 0 && (
          <>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th></th>
                    <th>Customer</th>
                    <th>Status</th>
                    <th>Score</th>
                    <th>Severity</th>
                    <th>Findings</th>
                    <th>Damage</th>
                    <th>Created</th>
                  </tr>
                </thead>
                <tbody>
                  {result.items.map((row) => (
                    <tr
                      key={row.id}
                      className="clickable"
                      onClick={() => navigate(`/inspections/${row.id}`)}
                    >
                      <td style={{ width: 46 }}>
                        {row.thumbnail_url ? (
                          <img
                            src={row.thumbnail_url}
                            alt=""
                            style={{ width: 36, height: 36, objectFit: 'cover', borderRadius: 6, display: 'block' }}
                          />
                        ) : (
                          <div style={{ width: 36, height: 36, borderRadius: 6, background: 'var(--surface-2)' }} />
                        )}
                      </td>
                      <td className="small">
                        {row.customer_name ? (
                          <>
                            {row.customer_name}
                            {row.vehicle_type && (
                              <span className="muted"> · {row.vehicle_type}</span>
                            )}
                          </>
                        ) : (
                          <span className="muted">—</span>
                        )}
                      </td>
                      <td><StatusBadge status={row.status} /></td>
                      <td><strong>{row.damage_score}</strong><span className="muted small">/100</span></td>
                      <td><SeverityBadge severity={row.overall_severity} /></td>
                      <td>{row.total_detections}</td>
                      <td>
                        <div className="row" style={{ gap: 4 }}>
                          {(row.damage_summary || [])
                            .filter((entry) => entry.count > 0)
                            .map((entry) => (
                              <DamageBadge
                                key={entry.class_key}
                                label={`${entry.label} ${entry.count}`}
                                color={colours[entry.class_key] || entry.color_hex}
                              />
                            ))}
                          {(row.damage_summary || []).every((entry) => entry.count === 0) && (
                            <span className="muted small">clean</span>
                          )}
                        </div>
                      </td>
                      <td className="small muted">{formatDateTime(row.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="spread" style={{ marginTop: 13 }}>
              <span className="muted small">
                Page {result.page} of {result.total_pages}
              </span>
              <div className="row">
                <button
                  className="btn-sm"
                  disabled={result.page <= 1}
                  onClick={() => setPage((value) => value - 1)}
                >
                  ← Previous
                </button>
                <button
                  className="btn-sm"
                  disabled={!result.has_next}
                  onClick={() => setPage((value) => value + 1)}
                >
                  Next →
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
