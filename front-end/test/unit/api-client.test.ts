import { describe, expect, it, vi } from 'vitest'
import { createApiClient } from '../../app/composables/useApi'
import { ApiError } from '../../app/utils/api-errors'

type Step = { status: number, body?: unknown, text?: string } | 'network'

function fakeFetch(steps: Step[]) {
  const calls: { url: string, auth: string | null }[] = []
  const fetchImpl: typeof fetch = async (input, init) => {
    const req = input instanceof Request ? input : new Request(input, init)
    calls.push({ url: req.url, auth: req.headers.get('authorization') })
    const step = steps.shift()
    if (!step) throw new Error('unexpected call')
    if (step === 'network') throw new TypeError('Failed to fetch')
    if (step.text !== undefined) return new Response(step.text, { status: step.status, headers: { 'content-type': 'text/plain' } })
    return new Response(JSON.stringify(step.body ?? null), { status: step.status, headers: { 'content-type': 'application/json' } })
  }
  return { fetchImpl, calls }
}

function session(opts: { token?: string | null, refreshed?: boolean } = {}) {
  let token = opts.token === undefined ? 'tok-1' : opts.token
  return {
    getAccessToken: vi.fn(async () => token),
    refresh: vi.fn(async () => {
      if (opts.refreshed) {
        token = 'tok-2'
        return true
      }
      return false
    }),
    onExpired: vi.fn(async () => {}),
  }
}

describe('createApiClient', () => {
  it('sends Bearer token and returns typed data', async () => {
    const { fetchImpl, calls } = fakeFetch([{ status: 200, body: [{ symbol: 'BTCUSDT', created_at: null }] }])
    const s = session()
    const api = createApiClient('http://api', s, fetchImpl)
    const data = await api.get('/api/v1/symbols')
    expect(data).toEqual([{ symbol: 'BTCUSDT', created_at: null }])
    expect(calls[0]?.auth).toBe('Bearer tok-1')
    expect(calls[0]?.url).toBe('http://api/api/v1/symbols')
  })

  it('/health never sends a token', async () => {
    const { fetchImpl, calls } = fakeFetch([{ status: 200, body: { status: 'ok', version: '0.1.0' } }])
    const s = session()
    await createApiClient('http://api', s, fetchImpl).get('/health')
    expect(calls[0]?.auth).toBeNull()
    expect(s.getAccessToken).not.toHaveBeenCalled()
  })

  it('401 → refresh → retry with the new token', async () => {
    const { fetchImpl, calls } = fakeFetch([
      { status: 401, body: { detail: 'Invalid or expired token' } },
      { status: 200, body: [] },
    ])
    const s = session({ refreshed: true })
    const data = await createApiClient('http://api', s, fetchImpl).get('/api/v1/klines/{timeframe}', { params: { path: { timeframe: '1h' }, query: { symbol: 'BTCUSDT' } } })
    expect(data).toEqual([])
    expect(s.refresh).toHaveBeenCalledTimes(1)
    expect(calls.map(c => c.auth)).toEqual(['Bearer tok-1', 'Bearer tok-2'])
    expect(calls[1]?.url).toContain('/api/v1/klines/1h?symbol=BTCUSDT')
    expect(s.onExpired).not.toHaveBeenCalled()
  })

  it('401 with failed refresh → onExpired once and ApiError(unauthorized)', async () => {
    const { fetchImpl } = fakeFetch([{ status: 401, body: { detail: 'Invalid or expired token' } }])
    const s = session({ refreshed: false })
    const api = createApiClient('http://api', s, fetchImpl)
    await expect(api.get('/api/v1/symbols')).rejects.toMatchObject({ kind: 'unauthorized', status: 401 })
    expect(s.onExpired).toHaveBeenCalledTimes(1)
  })

  it('5xx plain text → ApiError(server) with request label', async () => {
    const { fetchImpl } = fakeFetch([{ status: 503, text: 'Service Unavailable' }])
    const api = createApiClient('http://api', session(), fetchImpl)
    const err = await api.get('/api/v1/features/{timeframe}', { params: { path: { timeframe: '1d' }, query: { symbol: 'ETHUSDT' } } }).catch(e => e)
    expect(err).toBeInstanceOf(ApiError)
    expect(err.kind).toBe('server')
    expect(err.request).toBe('GET /features/1d')
  })

  it('422 → ApiError(validation) with details', async () => {
    const detail = [{ loc: ['query', 'limit'], msg: 'less than or equal to 1000', type: 'less_than_equal' }]
    const { fetchImpl } = fakeFetch([{ status: 422, body: { detail } }])
    const err = await createApiClient('http://api', session(), fetchImpl).get('/api/v1/symbols').catch(e => e)
    expect(err.kind).toBe('validation')
    expect(err.details).toEqual(detail)
  })

  it('network failure → ApiError(network)', async () => {
    const { fetchImpl } = fakeFetch(['network'])
    const err = await createApiClient('http://api', session(), fetchImpl).get('/api/v1/symbols').catch(e => e)
    expect(err.kind).toBe('network')
    expect(err.status).toBeNull()
  })

  it('PUT sends body with Bearer token and returns the saved document', async () => {
    const saved = { display_name: 'Gabriel', email: 'g@x.dev', notifications: { enabled: true, channel: 'email', topics: {} }, chart: { hollow_up_candles: true } }
    const { fetchImpl, calls } = fakeFetch([{ status: 200, body: saved }])
    const api = createApiClient('http://api', session(), fetchImpl)
    const data = await api.put('/api/v1/preferences', { body: { display_name: 'Gabriel' } })
    expect(data).toEqual(saved)
    expect(calls[0]?.auth).toBe('Bearer tok-1')
    expect(calls[0]?.url).toBe('http://api/api/v1/preferences')
  })

  it('PUT 401 → refresh → retry preserves the body', async () => {
    const { fetchImpl, calls } = fakeFetch([
      { status: 401, body: { detail: 'Invalid or expired token' } },
      { status: 200, body: { display_name: 'G' } },
    ])
    const s = session({ refreshed: true })
    const data = await createApiClient('http://api', s, fetchImpl).put('/api/v1/preferences', { body: { display_name: 'G' } })
    expect(data).toEqual({ display_name: 'G' })
    expect(calls.map(c => c.auth)).toEqual(['Bearer tok-1', 'Bearer tok-2'])
    expect(s.onExpired).not.toHaveBeenCalled()
  })

  it('PUT 422 → ApiError(validation) with PUT label', async () => {
    const detail = [{ loc: ['body', 'phone'], msg: 'String should match pattern', type: 'string_pattern_mismatch' }]
    const { fetchImpl } = fakeFetch([{ status: 422, body: { detail } }])
    const err = await createApiClient('http://api', session(), fetchImpl)
      .put('/api/v1/preferences', { body: { phone: 'x' } })
      .catch(e => e)
    expect(err.kind).toBe('validation')
    expect(err.request).toBe('PUT /preferences')
  })
})
