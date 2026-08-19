import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Alert, ErrorAlert, Spinner } from '../components/common.jsx'
import * as api from '../api/client.js'

const MAX_BYTES = 10 * 1024 * 1024
const MIN_DIMENSION = 320
const ALLOWED = ['image/jpeg', 'image/png', 'image/webp']

/** The five sides the API accepts, in the order it reports them. */
const VIEWS = [
  { key: 'front', label: 'Front', hint: 'Bonnet, bumper, headlights' },
  { key: 'back', label: 'Back', hint: 'Boot, rear bumper, taillights' },
  { key: 'left', label: 'Left', hint: 'Full left flank' },
  { key: 'right', label: 'Right', hint: 'Full right flank' },
  { key: 'top', label: 'Top', hint: 'Roof and windscreen' },
]

const STEPS = [
  { key: 'sign', label: 'Request Cloudinary signature', endpoint: 'POST /uploads/signature' },
  { key: 'upload', label: 'Upload photos to Cloudinary', endpoint: 'POST cloudinary.com/…/upload' },
  { key: 'create', label: 'Create inspection', endpoint: 'POST /inspections' },
  { key: 'analyse', label: 'Model analyses the photos', endpoint: 'GET /inspections/{id}/status' },
]

/** Read a local file's pixel dimensions so tiny images are caught before upload. */
function readDimensions(file) {
  return new Promise((resolve) => {
    const url = URL.createObjectURL(file)
    const probe = new Image()
    probe.onload = () => {
      resolve({ width: probe.naturalWidth, height: probe.naturalHeight, preview: url })
    }
    probe.onerror = () => resolve({ width: 0, height: 0, preview: url })
    probe.src = url
  })
}

export default function NewInspectionPage() {
  const navigate = useNavigate()

  // One photo per view: `images` in the request is keyed the same way.
  const [shots, setShots] = useState({})
  const [customerName, setCustomerName] = useState('')
  const [vehicleType, setVehicleType] = useState('')
  const [vehicleTypes, setVehicleTypes] = useState([])
  const [presets, setPresets] = useState([])
  const [preset, setPreset] = useState('balanced')
  const [dragOver, setDragOver] = useState(null)
  const [stage, setStage] = useState('idle')
  const [error, setError] = useState(null)
  const [inspection, setInspection] = useState(null)
  const [statusText, setStatusText] = useState('')

  // Release the object URLs created for previews when the page goes away.
  useEffect(
    () => () => Object.values(shots).forEach((shot) => URL.revokeObjectURL(shot.preview)),
    [],
  )

  // Presets and body styles come from the backend, so the thresholds and the
  // allowed values are defined in one place and cannot drift from the API.
  useEffect(() => {
    api
      .getDetectionPresets()
      .then((data) => {
        setPresets(data.items)
        setPreset(data.default)
      })
      .catch(() => {})

    api
      .getVehicleTypes()
      .then((data) => {
        setVehicleTypes(data.items)
        setVehicleType(data.items[0]?.key ?? '')
      })
      .catch(() => {})
  }, [])

  const busy = stage !== 'idle' && stage !== 'error'
  const chosen = VIEWS.filter((view) => shots[view.key])
  const ready = chosen.length > 0 && customerName.trim() !== '' && vehicleType !== '' && !busy

  async function setShot(view, file) {
    if (!file) return

    if (!ALLOWED.includes(file.type)) {
      setError({ code: 'CLIENT_VALIDATION', message: `${file.name}: unsupported type.` })
      return
    }
    if (file.size > MAX_BYTES) {
      setError({ code: 'CLIENT_VALIDATION', message: `${file.name}: larger than 10 MB.` })
      return
    }

    const info = await readDimensions(file)
    if (Math.min(info.width, info.height) < MIN_DIMENSION) {
      URL.revokeObjectURL(info.preview)
      setError({
        code: 'CLIENT_VALIDATION',
        message: `${file.name}: ${info.width}×${info.height} is below ${MIN_DIMENSION}px.`,
      })
      return
    }

    setError(null)
    setShots((current) => {
      // Replacing a slot: drop the previous preview so it is not leaked.
      if (current[view]) URL.revokeObjectURL(current[view].preview)
      return {
        ...current,
        [view]: { file, preview: info.preview, width: info.width, height: info.height, progress: 0 },
      }
    })
  }

  function removeShot(view) {
    setShots((current) => {
      if (current[view]) URL.revokeObjectURL(current[view].preview)
      const { [view]: _removed, ...rest } = current
      return rest
    })
  }

  function setProgress(view, progress) {
    setShots((current) =>
      current[view] ? { ...current, [view]: { ...current[view], progress } } : current,
    )
  }

  async function run() {
    setError(null)
    setInspection(null)

    try {
      // 1. One signature covers this batch: the folder and timestamp are fixed
      //    for the whole submission, which is exactly what the backend signed.
      setStage('sign')
      const signature = await api.getUploadSignature()

      // 2. Upload each photo straight to Cloudinary, keeping the view it belongs to.
      setStage('upload')
      const images = {}
      for (const view of chosen) {
        const result = await api.uploadToCloudinary(shots[view.key].file, signature, (progress) =>
          setProgress(view.key, progress),
        )
        setProgress(view.key, 100)
        images[view.key] = result.secure_url
      }

      // 3. Hand the URLs to the backend, keyed by view. It derives the Cloudinary
      //    public id from the URL, so nothing else about the upload is sent.
      setStage('create')
      const created = await api.createInspection(
        {
          customer_name: customerName.trim(),
          vehicle_type: vehicleType,
          images,
          settings: { preset },
        },
        // An idempotency key makes a retry or double click safe.
        `ui-${crypto.randomUUID()}`,
      )
      setInspection(created)

      // 4. Poll until the model finishes.
      setStage('analyse')
      const started = Date.now()
      let finished = null
      while (Date.now() - started < 5 * 60 * 1000) {
        const status = await api.getInspectionStatus(created.id)
        setStatusText(
          `${status.status} · ${status.total_detections} detection(s) · ${Math.round(
            (Date.now() - started) / 1000,
          )}s elapsed`,
        )
        if (status.is_finished) {
          finished = status
          break
        }
        await new Promise((resolve) => setTimeout(resolve, 2000))
      }

      if (!finished) throw new Error('Timed out waiting for the model. Check the backend logs.')

      setStage('done')
      navigate(`/inspections/${created.id}`)
    } catch (caught) {
      setError(caught)
      setStage('error')
    }
  }

  function stepState(key) {
    const order = STEPS.map((step) => step.key)
    if (stage === 'error') {
      const failedAt = order.indexOf(stage)
      return order.indexOf(key) < failedAt ? 'done' : 'failed'
    }
    if (stage === 'done') return 'done'
    const currentIndex = order.indexOf(stage)
    const thisIndex = order.indexOf(key)
    if (currentIndex === -1) return ''
    if (thisIndex < currentIndex) return 'done'
    if (thisIndex === currentIndex) return 'active'
    return ''
  }

  return (
    <div className="page">
      <div className="page-head">
        <h1>New Inspection</h1>
        <p>
          One photo per side of the vehicle. They go straight to Cloudinary using a signature issued
          by the backend, then the model analyses them.
        </p>
      </div>

      <ErrorAlert error={error} />

      <div className="grid grid-2">
        <div>
          <div className="card">
            <div className="card-head">
              <h2>Customer &amp; vehicle</h2>
              <span className="muted small mono">required</span>
            </div>
            <div className="field-row">
              <div className="field">
                <label>Customer name</label>
                <input
                  value={customerName}
                  onChange={(event) => setCustomerName(event.target.value)}
                  placeholder="test"
                  disabled={busy}
                />
              </div>
              <div className="field">
                <label>
                  Body style <span className="muted small">GET /vehicle-types</span>
                </label>
                <select
                  value={vehicleType}
                  onChange={(event) => setVehicleType(event.target.value)}
                  disabled={busy || vehicleTypes.length === 0}
                >
                  {vehicleTypes.map((type) => (
                    <option key={type.key} value={type.key}>
                      {type.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-head">
              <h2>Photos</h2>
              <span className="muted small">
                {chosen.length} / {VIEWS.length} sides
              </span>
            </div>

            <p className="muted small" style={{ marginBottom: 10 }}>
              JPG, PNG or WebP · max 10 MB · at least {MIN_DIMENSION}px on the short side. Any side
              you skip is simply left out of the report.
            </p>

            <div className="stack">
              {VIEWS.map((view) => {
                const shot = shots[view.key]
                return (
                  <div
                    key={view.key}
                    className={`detection-row${dragOver === view.key ? ' hot' : ''}`}
                    style={{ alignItems: 'center', gap: 11 }}
                    onDragOver={(event) => {
                      event.preventDefault()
                      if (!busy) setDragOver(view.key)
                    }}
                    onDragLeave={() => setDragOver(null)}
                    onDrop={(event) => {
                      event.preventDefault()
                      setDragOver(null)
                      if (!busy) setShot(view.key, event.dataTransfer.files?.[0])
                    }}
                  >
                    {shot ? (
                      <div className="thumb" style={{ width: 74, flex: '0 0 74px' }}>
                        <img src={shot.preview} alt={view.label} />
                      </div>
                    ) : (
                      <div
                        className="dropzone"
                        style={{
                          width: 74,
                          flex: '0 0 74px',
                          height: 56,
                          padding: 0,
                          display: 'grid',
                          placeItems: 'center',
                        }}
                      >
                        <span className="muted small">—</span>
                      </div>
                    )}

                    <span style={{ flex: 1 }}>
                      <span className="row" style={{ gap: 7 }}>
                        <strong className="small">{view.label}</strong>
                        <span className="badge status-queued mono">{view.key}</span>
                      </span>
                      <span className="muted small">
                        {shot ? `${shot.width}×${shot.height}` : view.hint}
                      </span>
                      {shot && shot.progress > 0 && shot.progress < 100 && (
                        <div className="progress" style={{ marginTop: 4 }}>
                          <div className="progress-bar" style={{ width: `${shot.progress}%` }} />
                        </div>
                      )}
                    </span>

                    <span className="row" style={{ gap: 6 }}>
                      <label className="btn-secondary small" style={{ cursor: busy ? 'default' : 'pointer' }}>
                        {shot ? 'Replace' : 'Choose'}
                        <input
                          type="file"
                          accept={ALLOWED.join(',')}
                          hidden
                          disabled={busy}
                          onChange={(event) => {
                            setShot(view.key, event.target.files?.[0])
                            event.target.value = ''
                          }}
                        />
                      </label>
                      {shot && !busy && (
                        <button className="btn-secondary small" onClick={() => removeShot(view.key)}>
                          ×
                        </button>
                      )}
                    </span>
                  </div>
                )
              })}
            </div>
          </div>

          <div className="card">
            <div className="card-head">
              <h2>Detection sensitivity</h2>
              <span className="muted small mono">GET /detection-presets</span>
            </div>

            <p className="muted small" style={{ marginBottom: 10 }}>
              The threshold decides what gets reported. Faint dents and cracks often score
              0.15–0.30, so <strong>Balanced</strong> can leave them out. If damage you can see is
              missing from the report, run it again on <strong>Sensitive</strong>.
            </p>

            <div className="stack">
              {presets.map((option) => (
                <label
                  key={option.key}
                  className={`detection-row${preset === option.key ? ' hot' : ''}`}
                  style={{ cursor: busy ? 'default' : 'pointer', alignItems: 'flex-start' }}
                >
                  <input
                    type="radio"
                    name="preset"
                    value={option.key}
                    checked={preset === option.key}
                    disabled={busy}
                    onChange={() => setPreset(option.key)}
                    style={{ width: 'auto', marginTop: 3 }}
                  />
                  <span style={{ flex: 1 }}>
                    <span className="row" style={{ gap: 7 }}>
                      <strong className="small">{option.label}</strong>
                      <span className="badge status-queued mono">conf {option.confidence}</span>
                      {option.is_default && <span className="muted small">default</span>}
                    </span>
                    <span className="muted small">{option.description}</span>
                  </span>
                </label>
              ))}
            </div>
          </div>
        </div>

        <div>
          <div className="card">
            <div className="card-head">
              <h2>What happens next</h2>
            </div>

            <div className="timeline">
              {STEPS.map((step, index) => {
                const state = stepState(step.key)
                return (
                  <div className={`timeline-step ${state}`} key={step.key}>
                    <div className="timeline-dot">
                      {state === 'done' ? '✓' : state === 'failed' ? '!' : index + 1}
                    </div>
                    <div>
                      <div className="timeline-label">
                        {step.label}
                        {state === 'active' && <span style={{ marginLeft: 8 }}><Spinner /></span>}
                      </div>
                      <div className="timeline-note mono">{step.endpoint}</div>
                      {step.key === 'analyse' && stage === 'analyse' && statusText && (
                        <div className="timeline-note">{statusText}</div>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>

            <button
              className="btn-primary btn-lg"
              style={{ width: '100%', marginTop: 6 }}
              disabled={!ready}
              onClick={run}
            >
              {busy ? <Spinner /> : `Analyse ${chosen.length || ''} photo${chosen.length === 1 ? '' : 's'}`}
            </button>

            {!busy && customerName.trim() === '' && chosen.length > 0 && (
              <p className="muted small" style={{ marginTop: 8 }}>
                Add a customer name to continue.
              </p>
            )}

            {inspection && (
              <p className="muted small mono" style={{ marginTop: 10 }}>
                {inspection.id}
              </p>
            )}
          </div>

          <Alert kind="info">
            The model runs on the CPU, so allow a few seconds per photo. A five-photo inspection
            typically takes around 30 seconds.
          </Alert>
        </div>
      </div>
    </div>
  )
}
