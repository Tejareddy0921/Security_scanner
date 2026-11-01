import { apiRequest } from './api.js'

const labelDetails = {
  scam: { level: 'high', title: 'Likely a scam' },
  suspicious: { level: 'medium', title: 'Worth a closer look' },
  not_scam: { level: 'low', title: 'Looks low risk' },
}

function mapDetection(detection) {
  if (!detection || typeof detection !== 'object') {
    throw new Error('The backend returned an invalid scan result.')
  }

  const { level, title } = labelDetails[detection.label] ?? labelDetails.suspicious
  const recommendations = Array.isArray(detection.recommendations)
    ? detection.recommendations.filter((item) => typeof item === 'string' && item.trim())
    : []
  const riskFactors = Array.isArray(detection.risk_factors)
    ? detection.risk_factors.filter((item) => typeof item === 'string' && item.trim())
    : []
  const explanation = typeof detection.explanation === 'string' ? detection.explanation : ''
  const category = typeof detection.scam_type === 'string' && detection.scam_type.trim()
    ? detection.scam_type.trim().replace(/[_-]+/g, ' ').replace(/\b\w/g, (letter) => letter.toUpperCase())
    : ''
  const confidence = detection.confidence_score
  const score = typeof confidence === 'number' && Number.isFinite(confidence)
    ? Math.round(Math.min(1, Math.max(0, confidence)) * 100)
    : null
  const guidance = [explanation, ...recommendations].filter(Boolean).join(' ')

  return {
    id: detection.detection_id,
    text: typeof detection.content === 'string' ? detection.content : '',
    level,
    title,
    category,
    score,
    explanation,
    riskFactors,
    recommendations,
    guidance,
    signals: riskFactors.length,
    checkedAt: detection.created_at,
  }
}

export async function analyzeMessage(message, token, signal) {
  const content = String(message ?? '').trim()
  if (!content) throw new Error('Paste a message or link to check.')

  const detection = await apiRequest('/detection/analyze', {
    method: 'POST',
    token,
    signal,
    body: { content, source: 'other' },
  })
  return mapDetection(detection)
}

export async function getScanHistory(token) {
  const detections = await apiRequest('/detection/history', { token })
  if (!Array.isArray(detections)) throw new Error('The backend returned invalid scan history.')
  return detections.map(mapDetection)
}
