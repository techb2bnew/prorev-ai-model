import { useState } from 'react'
import { useApiLog } from '../context/ApiLogContext.jsx'

/**
 * Live list of every API call the app has made.
 *
 * Present so the integration is observable rather than implied - each row is a
 * real request, with its status, duration and the backend's correlation id.
 */
export default function ApiLogPanel() {
  const { entries, clear } = useApiLog()
  const [open, setOpen] = useState(true)

  const failures = entries.filter((entry) => !entry.ok).length

  return (
    <div className="api-panel">
      <div className="api-panel-head" onClick={() => setOpen((value) => !value)}>
        <div className="api-panel-title">
          <span>{open ? '▾' : '▸'}</span>
          <span>API Activity</span>
          <span className="badge status-completed">{entries.length}</span>
          {failures > 0 && <span className="badge status-failed">{failures} failed</span>}
        </div>
        <div className="row">
          <span className="muted small">every request this UI sends</span>
          <button
            className="btn-sm btn-ghost"
            onClick={(event) => {
              event.stopPropagation()
              clear()
            }}
          >
            Clear
          </button>
        </div>
      </div>

      {open && (
        <div className="api-panel-body">
          {entries.length === 0 && (
            <div className="muted small" style={{ padding: '10px 14px' }}>
              No calls yet — navigate around and they will appear here.
            </div>
          )}
          {entries.map((entry) => (
            <div className="api-row" key={entry.id} title={entry.correlationId ? `correlation id: ${entry.correlationId}` : ''}>
              <span className={`api-method m-${entry.method}`}>{entry.method}</span>
              <span className={`api-status s-${String(entry.status).charAt(0)}`}>
                {entry.status || 'ERR'}
              </span>
              <span className="api-url">
                {entry.url}
                {entry.note && <span className="api-note"> — {entry.note}</span>}
              </span>
              <span className="api-ms">{entry.ms}ms</span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
