import { useEffect, useState } from 'react'
import { Alert, DamageBadge, ErrorAlert, Spinner } from '../components/common.jsx'
import * as api from '../api/client.js'

/** Every endpoint, with the ones that are safe to call on demand wired up. */
const ENDPOINTS = [
  { method: 'GET', path: '/health', note: 'Liveness', auth: false, run: api.getHealth },
  { method: 'GET', path: '/health/ready', note: 'Database + model + Cloudinary', auth: false, run: api.getReadiness },
  { method: 'POST', path: '/auth/register', note: 'Create account', auth: false },
  { method: 'POST', path: '/auth/login', note: 'Issue tokens', auth: false },
  { method: 'POST', path: '/auth/refresh', note: 'Rotate access token', auth: true },
  { method: 'GET', path: '/auth/me', note: 'Current user', auth: true, run: api.getMe },
  { method: 'POST', path: '/uploads/signature', note: 'Signed Cloudinary upload', auth: true, run: () => api.getUploadSignature() },
  { method: 'POST', path: '/inspections', note: 'Submit photos → 202', auth: true },
  { method: 'GET', path: '/inspections', note: 'History, paginated', auth: true, run: () => api.listInspections({ page: 1, page_size: 3 }) },
  { method: 'GET', path: '/inspections/{id}', note: 'Full inspection + report', auth: true },
  { method: 'GET', path: '/inspections/{id}/status', note: 'Lightweight poll', auth: true },
  { method: 'GET', path: '/inspections/{id}/report', note: 'Report only', auth: true },
  { method: 'DELETE', path: '/inspections/{id}', note: 'Soft delete', auth: true },
  { method: 'GET', path: '/damage-types', note: 'The six classes + colours', auth: false, run: api.getDamageTypes },
  { method: 'GET', path: '/vehicle-types', note: 'Car body styles', auth: false, run: api.getVehicleTypes },
  { method: 'GET', path: '/detection-presets', note: 'Sensitivity modes', auth: false, run: api.getDetectionPresets },
  { method: 'GET', path: '/stats/summary', note: 'Dashboard counts', auth: true, run: api.getStatsSummary },
]

export default function HealthPage() {
  const [ready, setReady] = useState(null)
  const [types, setTypes] = useState([])
  const [error, setError] = useState(null)
  const [checking, setChecking] = useState(true)
  const [result, setResult] = useState(null)
  const [runningPath, setRunningPath] = useState(null)

  async function refresh() {
    setChecking(true)
    setError(null)
    try {
      const [readiness, damageTypes] = await Promise.all([api.getReadiness(), api.getDamageTypes()])
      setReady(readiness)
      setTypes(damageTypes.items)
    } catch (caught) {
      setError(caught)
    } finally {
      setChecking(false)
    }
  }

  useEffect(() => {
    refresh()
  }, [])

  async function tryEndpoint(endpoint) {
    setRunningPath(endpoint.path)
    setResult(null)
    try {
      const payload = await endpoint.run()
      setResult({ endpoint, ok: true, payload })
    } catch (caught) {
      setResult({ endpoint, ok: false, payload: { code: caught.code, message: caught.message } })
    } finally {
      setRunningPath(null)
    }
  }

  const checks = ready?.checks

  return (
    <div className="page">
      <div className="page-head spread">
        <div>
          <h1>System & API</h1>
          <p>Backend health, and every endpoint this UI talks to.</p>
        </div>
        <button onClick={refresh} disabled={checking}>
          {checking ? <Spinner /> : 'Re-check'}
        </button>
      </div>

      <ErrorAlert error={error} />

      <div className="grid grid-3">
        {['database', 'model', 'cloudinary'].map((key) => {
          const check = checks?.[key]
          const ok = check?.ok
          return (
            <div className="card" key={key}>
              <div className="spread">
                <h3 style={{ textTransform: 'capitalize' }}>{key}</h3>
                <span className={`badge ${ok ? 'status-completed' : 'status-failed'}`}>
                  {checking ? '…' : ok ? 'ok' : 'not ready'}
                </span>
              </div>
              {key === 'model' && check?.ok && (
                <p className="muted small mono" style={{ marginTop: 8 }}>
                  {check.backend} · {check.name} v{check.version}
                </p>
              )}
              {key === 'cloudinary' && (
                <p className="muted small" style={{ marginTop: 8 }}>
                  {check?.configured ? 'Credentials configured' : 'Credentials missing — uploads will fail'}
                </p>
              )}
              {check?.error && (
                <p className="small" style={{ marginTop: 8, color: 'var(--danger)' }}>{check.error}</p>
              )}
            </div>
          )
        })}
      </div>

      {ready && ready.status !== 'ready' && (
        <Alert kind="error" title="Backend not ready">
          The API reported <span className="mono">{ready.status}</span>. Inspections will fail until
          this is resolved.
        </Alert>
      )}

      <div className="card">
        <div className="card-head">
          <h2>Damage classes</h2>
          <span className="muted small mono">GET /damage-types</span>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Index</th>
                <th>Class</th>
                <th>Model label</th>
                <th>Key</th>
                <th>Critical</th>
                <th>Description</th>
              </tr>
            </thead>
            <tbody>
              {types.map((type) => (
                <tr key={type.class_key}>
                  <td className="mono">{type.model_class_index}</td>
                  <td><DamageBadge label={type.label} color={type.color_hex} /></td>
                  <td className="mono small">{type.model_label}</td>
                  <td className="mono small muted">{type.class_key}</td>
                  <td>{type.is_critical ? <span className="badge sev-severe">yes</span> : <span className="muted small">no</span>}</td>
                  <td className="small muted">{type.description}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card">
        <div className="card-head">
          <h2>Endpoints</h2>
          <span className="muted small">
            {ENDPOINTS.length} routes · press Run to call one and see the response
          </span>
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Method</th>
                <th>Path</th>
                <th>Purpose</th>
                <th>Auth</th>
                <th className="right">Try</th>
              </tr>
            </thead>
            <tbody>
              {ENDPOINTS.map((endpoint) => (
                <tr key={`${endpoint.method} ${endpoint.path}`}>
                  <td>
                    <span className={`api-method m-${endpoint.method} mono`}>{endpoint.method}</span>
                  </td>
                  <td className="mono small">/api/v1{endpoint.path}</td>
                  <td className="small muted">{endpoint.note}</td>
                  <td>
                    {endpoint.auth
                      ? <span className="badge status-processing">JWT</span>
                      : <span className="badge status-queued">public</span>}
                  </td>
                  <td className="right">
                    {endpoint.run ? (
                      <button
                        className="btn-sm"
                        disabled={runningPath === endpoint.path}
                        onClick={() => tryEndpoint(endpoint)}
                      >
                        {runningPath === endpoint.path ? <Spinner /> : 'Run'}
                      </button>
                    ) : (
                      <span className="muted small">used in flow</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {result && (
          <div style={{ marginTop: 14 }}>
            <div className="spread" style={{ marginBottom: 6 }}>
              <strong className="small mono">
                {result.endpoint.method} /api/v1{result.endpoint.path}
              </strong>
              <span className={`badge ${result.ok ? 'status-completed' : 'status-failed'}`}>
                {result.ok ? 'ok' : 'failed'}
              </span>
            </div>
            <pre
              className="mono"
              style={{
                maxHeight: 260, overflow: 'auto', background: 'var(--bg)',
                padding: 12, borderRadius: 8, margin: 0,
              }}
            >
              {JSON.stringify(result.payload, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  )
}
