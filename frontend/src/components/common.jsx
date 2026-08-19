/** Small presentational pieces shared across pages. */

export function Spinner() {
  return <span className="spinner" />
}

export function SeverityBadge({ severity }) {
  if (!severity) return <span className="muted small">—</span>
  return <span className={`badge sev-${severity}`}>{severity}</span>
}

export function StatusBadge({ status }) {
  const spinning = status === 'processing' || status === 'queued'
  return (
    <span className={`badge status-${status}`}>
      {spinning && <span className="spinner" style={{ width: 9, height: 9, borderWidth: 1.5 }} />}
      {status?.replace('_', ' ')}
    </span>
  )
}

export function DamageBadge({ label, color }) {
  return (
    <span className="badge" style={{ borderColor: color, color }}>
      <span className="dot" style={{ background: color }} />
      {label}
    </span>
  )
}

export function Alert({ kind = 'info', title, children }) {
  return (
    <div className={`alert alert-${kind}`}>
      {title && <strong>{title}</strong>}
      {children}
    </div>
  )
}

/** Renders an ApiError, including per-field validation messages when present. */
export function ErrorAlert({ error }) {
  if (!error) return null
  const fields = typeof error.fieldMessages === 'object' ? error.fieldMessages : []
  return (
    <Alert kind="error">
      <div>{error.message}</div>
      {error.code && error.code !== 'UNKNOWN' && (
        <div className="mono small" style={{ marginTop: 4, opacity: 0.75 }}>{error.code}</div>
      )}
      {fields.length > 0 && (
        <ul>
          {fields.map((message) => (
            <li key={message} className="small">{message}</li>
          ))}
        </ul>
      )}
    </Alert>
  )
}

export function Empty({ icon = '∅', title, children }) {
  return (
    <div className="empty">
      <div className="empty-icon">{icon}</div>
      <div style={{ fontWeight: 600, color: 'var(--text)' }}>{title}</div>
      {children && <p className="small" style={{ marginTop: 5 }}>{children}</p>}
    </div>
  )
}

export function Stat({ label, value, foot, color }) {
  return (
    <div className="stat">
      <div className="stat-label">{label}</div>
      <div className="stat-value" style={color ? { color } : undefined}>{value}</div>
      {foot && <div className="stat-foot">{foot}</div>}
    </div>
  )
}

const BAND_COLOURS = {
  none: '#8d9ab4',
  minor: '#7dd3fc',
  moderate: '#fbbf24',
  severe: '#f43f5e',
}

/** Circular 0-100 damage score dial. */
export function ScoreGauge({ score = 0, band = 'none', size = 84 }) {
  const radius = size / 2 - 4
  const circumference = 2 * Math.PI * radius
  const colour = BAND_COLOURS[band] || BAND_COLOURS.none
  const offset = circumference * (1 - Math.min(Math.max(score, 0), 100) / 100)

  return (
    <div className="gauge">
      <div className="gauge-ring" style={{ width: size, height: size }}>
        <svg width={size} height={size}>
          <circle className="gauge-ring-track" cx={size / 2} cy={size / 2} r={radius} />
          <circle
            className="gauge-ring-fill"
            cx={size / 2}
            cy={size / 2}
            r={radius}
            stroke={colour}
            strokeDasharray={circumference}
            strokeDashoffset={offset}
          />
        </svg>
        <div className="gauge-value" style={{ color: colour }}>{score}</div>
      </div>
      <div>
        <div className="stat-label">Damage score</div>
        <div style={{ fontWeight: 650, color: colour, textTransform: 'capitalize' }}>{band}</div>
        <div className="stat-foot">out of 100</div>
      </div>
    </div>
  )
}

export function formatDateTime(value) {
  if (!value) return '—'
  return new Date(value).toLocaleString(undefined, {
    day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
  })
}
