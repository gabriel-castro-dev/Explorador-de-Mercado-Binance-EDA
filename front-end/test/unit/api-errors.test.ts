import { describe, expect, it } from 'vitest'
import { ApiError, describeError, isApiError, networkError, normalizeApiError } from '../../app/utils/api-errors'

describe('normalizeApiError', () => {
  it('401 → unauthorized with generic message (string detail)', () => {
    const err = normalizeApiError(401, { detail: 'Invalid or expired token' }, 'GET /klines/1h')
    expect(err.kind).toBe('unauthorized')
    expect(err.status).toBe(401)
    expect(err.message).toMatch(/Sessão expirada/)
  })
  it('422 → validation with detail array preserved', () => {
    const detail = [{ loc: ['path', 'timeframe'], msg: 'Input should be 15m, 1h or 1d', type: 'enum' }]
    const err = normalizeApiError(422, { detail }, 'GET /klines/2h')
    expect(err.kind).toBe('validation')
    expect(err.details).toEqual(detail)
  })
  it('5xx → server even when body is plain text', () => {
    const err = normalizeApiError(503, 'Internal Server Error', 'GET /klines/1h')
    expect(err.kind).toBe('server')
    expect(describeError(err)).toBe('GET /klines/1h · 503')
  })
  it('other 4xx keeps the API detail when it is a string', () => {
    const err = normalizeApiError(404, { detail: 'Not Found' })
    expect(err.kind).toBe('client')
    expect(err.message).toBe('Not Found')
    expect(describeError(err)).toBe('HTTP 404')
  })
})

describe('networkError / isApiError', () => {
  it('has null status and a network kind', () => {
    const err = networkError('GET /symbols', new TypeError('fetch failed'))
    expect(err.kind).toBe('network')
    expect(err.status).toBeNull()
    expect(describeError(err)).toBe('GET /symbols · rede')
    expect(isApiError(err)).toBe(true)
    expect(isApiError(new Error('x'))).toBe(false)
    expect(err).toBeInstanceOf(ApiError)
  })
})
