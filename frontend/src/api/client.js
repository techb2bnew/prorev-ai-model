/**
 * Single place every HTTP call goes through.
 *
 * Two jobs beyond fetching: it attaches the JWT, and it reports every request
 * to a listener so the UI can show the API traffic live. That listener is how
 * the "API Activity" panel works - no call can bypass it.
 */

import { randomUUID } from '../utils/uuid'

const API_BASE = '/api/v1'

let authToken = localStorage.getItem('dd_token') || null
let logListener = null

export function setToken(token) {
  authToken = token
  if (token) localStorage.setItem('dd_token', token)
  else localStorage.removeItem('dd_token')
}

export function getToken() {
  return authToken
}

export function setLogListener(fn) {
  logListener = fn
}

/** Error carrying the backend's uniform { error: { code, message, details } } envelope. */
export class ApiError extends Error {
  constructor(status, payload) {
    const detail = payload?.error?.message || `Request failed with status ${status}`
    super(detail)
    this.name = 'ApiError'
    this.status = status
    this.code = payload?.error?.code || 'UNKNOWN'
    this.details = payload?.error?.details || null
  }

  /** Flatten Pydantic field errors into something displayable. */
  get fieldMessages() {
    const fields = this.details?.fields
    if (!Array.isArray(fields)) return []
    return fields.map((f) => `${f.field}: ${f.message}`)
  }
}

function emit(entry) {
  if (logListener) logListener({ ...entry, id: randomUUID(), at: new Date() })
}

async function request(method, path, { body, auth = true, headers = {} } = {}) {
  const started = performance.now()
  const url = `${API_BASE}${path}`

  const finalHeaders = { ...headers }
  if (body !== undefined) finalHeaders['Content-Type'] = 'application/json'
  if (auth && authToken) finalHeaders.Authorization = `Bearer ${authToken}`

  let response
  try {
    response = await fetch(url, {
      method,
      headers: finalHeaders,
      body: body === undefined ? undefined : JSON.stringify(body),
    })
  } catch (networkError) {
    emit({ method, url, status: 0, ms: Math.round(performance.now() - started), ok: false,
      note: 'network error - is the backend running?' })
    throw new Error(
      'Could not reach the API. Check the backend is running on the port the Vite proxy targets.',
    )
  }

  const ms = Math.round(performance.now() - started)

  // 204 and other empty bodies must not go through res.json().
  const text = await response.text()
  let payload = null
  if (text) {
    try {
      payload = JSON.parse(text)
    } catch {
      payload = { raw: text }
    }
  }

  emit({
    method,
    url,
    status: response.status,
    ms,
    ok: response.ok,
    correlationId: response.headers.get('X-Correlation-Id'),
    response: payload,
  })

  if (!response.ok) throw new ApiError(response.status, payload)
  return payload
}

/* ---------------- Health ---------------- */
export const getHealth = () => request('GET', '/health', { auth: false })
export const getReadiness = () => request('GET', '/health/ready', { auth: false })

/* ---------------- Auth ---------------- */
export const register = (body) => request('POST', '/auth/register', { body, auth: false })
export const login = (body) => request('POST', '/auth/login', { body, auth: false })
export const getMe = () => request('GET', '/auth/me')

/* ---------------- Uploads ---------------- */
export const getUploadSignature = (folder) =>
  request('POST', '/uploads/signature', { body: folder ? { folder } : {} })

/**
 * Upload one file straight to Cloudinary using a backend-issued signature.
 *
 * The parameters sent here must match exactly what the backend signed (folder
 * and timestamp) or Cloudinary rejects the signature.
 */
export async function uploadToCloudinary(file, signature, onProgress) {
  const form = new FormData()
  form.append('file', file)
  form.append('api_key', signature.api_key)
  form.append('timestamp', signature.timestamp)
  form.append('signature', signature.signature)
  form.append('folder', signature.folder)

  const started = performance.now()

  // XHR rather than fetch, because fetch cannot report upload progress.
  const result = await new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    xhr.open('POST', signature.upload_url)

    xhr.upload.onprogress = (event) => {
      if (event.lengthComputable && onProgress) {
        onProgress(Math.round((event.loaded / event.total) * 100))
      }
    }
    xhr.onload = () => {
      let parsed = null
      try {
        parsed = JSON.parse(xhr.responseText)
      } catch {
        parsed = null
      }
      if (xhr.status >= 200 && xhr.status < 300) resolve(parsed)
      else reject(new Error(parsed?.error?.message || `Cloudinary upload failed (${xhr.status})`))
    }
    xhr.onerror = () => reject(new Error('Network error while uploading to Cloudinary'))
    xhr.send(form)
  }).then(
    (value) => {
      emit({ method: 'POST', url: signature.upload_url, status: 200,
        ms: Math.round(performance.now() - started), ok: true,
        note: `uploaded ${file.name}`, response: { public_id: value?.public_id } })
      return value
    },
    (error) => {
      emit({ method: 'POST', url: signature.upload_url, status: 0,
        ms: Math.round(performance.now() - started), ok: false, note: error.message })
      throw error
    },
  )

  return result
}

/* ---------------- Inspections ---------------- */
export const createInspection = (body, idempotencyKey) =>
  request('POST', '/inspections', {
    body,
    headers: idempotencyKey ? { 'Idempotency-Key': idempotencyKey } : {},
  })

export const listInspections = (params = {}) => {
  const query = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== '' && value !== null && value !== undefined) query.set(key, value)
  })
  const suffix = query.toString()
  return request('GET', `/inspections${suffix ? `?${suffix}` : ''}`)
}

export const getInspection = (id) => request('GET', `/inspections/${id}`)
export const getInspectionStatus = (id) => request('GET', `/inspections/${id}/status`)
export const getInspectionReport = (id) => request('GET', `/inspections/${id}/report`)
export const deleteInspection = (id) => request('DELETE', `/inspections/${id}`)

/* ---------------- Reference data ---------------- */
export const getDamageTypes = () => request('GET', '/damage-types', { auth: false })
export const getVehicleTypes = () => request('GET', '/vehicle-types', { auth: false })
export const getDetectionPresets = () => request('GET', '/detection-presets', { auth: false })
export const getStatsSummary = () => request('GET', '/stats/summary')
