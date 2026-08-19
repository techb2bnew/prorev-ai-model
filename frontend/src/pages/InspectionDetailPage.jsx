import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import AnnotatedShot from '../components/AnnotatedShot.jsx'
import {
  Alert,
  DamageBadge,
  Empty,
  ErrorAlert,
  ScoreGauge,
  SeverityBadge,
  Spinner,
  Stat,
  StatusBadge,
  formatDateTime,
} from '../components/common.jsx'
import * as api from '../api/client.js'

export default function InspectionDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()

  const [data, setData] = useState(null)
  const [types, setTypes] = useState([])
  const [error, setError] = useState(null)
  const [hovered, setHovered] = useState(null)
  const [deleting, setDeleting] = useState(false)

  useEffect(() => {
    let cancelled = false
    let timer = null

    async function load() {
      try {
        const [detail, damageTypes] = await Promise.all([
          api.getInspection(id),
          types.length ? Promise.resolve({ items: types }) : api.getDamageTypes(),
        ])
        if (cancelled) return
        setData(detail)
        setTypes(damageTypes.items)

        // Still running? Come back shortly - covers arriving from a shared link
        // while the model is mid-analysis.
        if (!['completed', 'partial_success', 'failed'].includes(detail.status)) {
          timer = setTimeout(load, 2500)
        }
      } catch (caught) {
        if (!cancelled) setError(caught)
      }
    }

    load()
    return () => {
      cancelled = true
      if (timer) clearTimeout(timer)
    }
  }, [id])

  async function remove() {
    if (!window.confirm('Delete this inspection? It will be hidden from your history.')) return
    setDeleting(true)
    try {
      await api.deleteInspection(id)
      navigate('/history')
    } catch (caught) {
      setError(caught)
      setDeleting(false)
    }
  }

  if (error) {
    return (
      <div className="page">
        <ErrorAlert error={error} />
        <button onClick={() => navigate('/history')}>Back to history</button>
      </div>
    )
  }

  if (!data) {
    return (
      <div className="page">
        <div className="row"><Spinner /> <span className="muted">Loading inspection…</span></div>
      </div>
    )
  }

  const report = data.report
  const colours = Object.fromEntries(types.map((type) => [type.class_key, type.color_hex]))
  const found = report.damage_summary.filter((row) => row.count > 0)
  const running = !['completed', 'partial_success', 'failed'].includes(data.status)

  return (
    <div className="page">
      <div className="page-head spread">
        <div>
          <h1>{data.customer_name || 'Inspection'}</h1>
          <p>
            {[formatDateTime(data.created_at), data.vehicle_type].filter(Boolean).join(' · ')}
          </p>
        </div>
        <div className="row">
          <StatusBadge status={data.status} />
          <button className="btn-sm" onClick={() => navigate('/history')}>Back</button>
          <button className="btn-sm btn-danger" onClick={remove} disabled={deleting}>
            {deleting ? <Spinner /> : 'Delete'}
          </button>
        </div>
      </div>

      {running && (
        <Alert kind="info">
          <div className="row">
            <Spinner /> The model is still working on this inspection. This page refreshes itself.
          </div>
        </Alert>
      )}

      {data.error && (
        <Alert kind="error" title={data.error.code}>
          <div>{data.error.message}</div>
        </Alert>
      )}

      {report.partial_success && (
        <Alert kind="warn">
          Some photos could not be analysed. The report below is based on the
          {' '}{report.images_analysed} of {report.images_submitted} that worked.
        </Alert>
      )}

      {report.below_threshold_count > 0 && (
        <Alert kind="warn" title={`${report.below_threshold_count} finding(s) below the confidence threshold`}>
          <div>
            The model also saw {report.below_threshold_count} area
            {report.below_threshold_count === 1 ? '' : 's'} of damage it was not confident enough
            about to report at{' '}
            <span className="mono">conf {report.detection_settings?.confidence}</span>
            {report.detection_preset ? ` (${report.detection_preset})` : ''}. If damage you can see
            is missing below, run the same photos again on a higher sensitivity.
          </div>
          <div style={{ marginTop: 8 }}>
            <button className="btn-sm" onClick={() => navigate('/inspect')}>
              New inspection with Sensitive →
            </button>
          </div>
        </Alert>
      )}

      {report.image_quality_warnings?.length > 0 && (
        <Alert kind="warn" title="Photo quality">
          <ul>
            {report.image_quality_warnings.map((warning, index) => (
              <li key={index} className="small">Photo {warning.sequence_no + 1}: {warning.warning}</li>
            ))}
          </ul>
        </Alert>
      )}

      <div className="card">
        <div className="grid grid-4">
          <div className="stat">
            <ScoreGauge score={report.damage_score} band={report.overall_severity} />
          </div>
          <Stat
            label="Findings"
            value={report.total_detections}
            foot={report.total_detections === 0 ? 'no damage detected' : 'across all photos'}
          />
          <Stat
            label="Affected area"
            value={`${report.total_area_percent ?? 0}%`}
            foot="average per photo"
          />
          <Stat
            label="Photos analysed"
            value={`${report.images_analysed}/${report.images_submitted}`}
            foot={report.processing_ms ? `${(report.processing_ms / 1000).toFixed(1)}s processing` : ''}
          />
        </div>
      </div>

      <div className="card">
        <div className="card-head">
          <h2>Damage summary</h2>
          <div className="row">
            {report.detection_preset && (
              <span className="badge status-processing">
                {report.detection_preset} · conf {report.detection_settings?.confidence} · iou{' '}
                {report.detection_settings?.iou} · imgsz {report.detection_settings?.input_size}
              </span>
            )}
            <span className="muted small">
              {report.model.name} v{report.model.version}
            </span>
          </div>
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Damage type</th>
                <th>Found</th>
                <th>Worst severity</th>
                <th>Area</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {report.damage_summary.map((row) => (
                <tr key={row.class_key} style={row.count === 0 ? { opacity: 0.45 } : undefined}>
                  <td><DamageBadge label={row.label} color={row.color_hex} /></td>
                  <td>{row.count === 0 ? <span className="muted">none</span> : <strong>{row.count}</strong>}</td>
                  <td><SeverityBadge severity={row.max_severity} /></td>
                  <td className="mono">{row.count ? `${row.total_area_percent}%` : '—'}</td>
                  <td className="right">
                    {row.is_critical && <span className="badge sev-severe">critical</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div className="card">
        <div className="card-head">
          <h2>Photos and detections</h2>
          <span className="muted small">hover a box or a row to link them</span>
        </div>

        {report.total_detections === 0 && !running && (
          <Empty icon="✓" title="No damage detected">
            The model found nothing on {report.images_analysed} photo
            {report.images_analysed === 1 ? '' : 's'}.
          </Empty>
        )}

        <div className="grid grid-2">
          {report.images.map((image) => (
            <div key={image.inspection_image_id} className="stack">
              <div className="spread">
                <div className="row">
                  <strong className="small">
                    Photo {image.sequence_no + 1}
                    {image.view_angle ? ` · ${image.view_angle}` : ''}
                  </strong>
                  {image.status === 'failed' && <span className="badge status-failed">failed</span>}
                </div>
                <span className="muted small mono">
                  {image.dimensions?.width}×{image.dimensions?.height}
                </span>
              </div>

              {image.status === 'failed' ? (
                <Alert kind="error">{image.failure_reason}</Alert>
              ) : (
                <>
                  <AnnotatedShot
                    image={image}
                    colours={colours}
                    activeId={hovered}
                    onHover={setHovered}
                  />

                  {image.detections.length === 0 ? (
                    <p className="muted small">No damage found on this photo.</p>
                  ) : (
                    <div className="stack">
                      {image.detections.map((detection) => (
                        <div
                          key={detection.id}
                          className={`detection-row${hovered === detection.id ? ' hot' : ''}`}
                          onMouseEnter={() => setHovered(detection.id)}
                          onMouseLeave={() => setHovered(null)}
                        >
                          <span
                            className="dot"
                            style={{ background: colours[detection.class_key] || '#38bdf8' }}
                          />
                          <strong className="small" style={{ flex: 1 }}>{detection.label}</strong>
                          <SeverityBadge severity={detection.severity} />
                          <span className="mono muted">
                            {(detection.confidence * 100).toFixed(1)}%
                          </span>
                        </div>
                      ))}
                    </div>
                  )}

                  {image.quality && (
                    <p className="muted small mono">
                      blur {image.quality.blur_score} · brightness {image.quality.brightness}
                      {image.quality.is_blurry && ' · flagged blurry'}
                    </p>
                  )}
                </>
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="card">
        <div className="card-head">
          <h3>Raw report payload</h3>
          <span className="muted small mono">GET /api/v1/inspections/{id}</span>
        </div>
        <details>
          <summary className="small muted" style={{ cursor: 'pointer' }}>
            Show the exact JSON the API returned
          </summary>
          <pre
            className="mono"
            style={{
              marginTop: 10, maxHeight: 320, overflow: 'auto',
              background: 'var(--bg)', padding: 12, borderRadius: 8,
            }}
          >
            {JSON.stringify(data, null, 2)}
          </pre>
        </details>
      </div>
    </div>
  )
}
