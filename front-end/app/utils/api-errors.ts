/**
 * Normalização dos erros da API FastAPI num único tipo.
 * Formatos reais (back-end/app/controllers): 401 `{detail: string}` + WWW-Authenticate;
 * 422 `{detail: ValidationError[]}`; 5xx texto puro (sem handler); rede → sem status.
 */

export type ApiErrorKind = 'unauthorized' | 'validation' | 'server' | 'network' | 'client'

export class ApiError extends Error {
  readonly kind: ApiErrorKind
  readonly status: number | null
  readonly details?: unknown
  /** Descrição mono para a UI, ex.: `GET /klines/1h · 503`. */
  readonly request?: string

  constructor(kind: ApiErrorKind, message: string, opts: { status?: number | null, details?: unknown, request?: string } = {}) {
    super(message)
    this.name = 'ApiError'
    this.kind = kind
    this.status = opts.status ?? null
    this.details = opts.details
    this.request = opts.request
  }
}

interface ValidationItem {
  loc?: (string | number)[]
  msg?: string
  type?: string
}

function readDetail(body: unknown): string | ValidationItem[] | undefined {
  if (body && typeof body === 'object' && 'detail' in body) {
    const detail = (body as { detail: unknown }).detail
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) return detail as ValidationItem[]
  }
  return undefined
}

export function normalizeApiError(status: number, body: unknown, request?: string): ApiError {
  const detail = readDetail(body)
  if (status === 401) {
    return new ApiError('unauthorized', 'Sessão expirada. Entre de novo para continuar.', { status, details: detail, request })
  }
  if (status === 422) {
    return new ApiError('validation', 'Parâmetros inválidos na requisição.', { status, details: Array.isArray(detail) ? detail : undefined, request })
  }
  if (status >= 500) {
    return new ApiError('server', 'A API não respondeu. Tente de novo em alguns segundos.', { status, request })
  }
  const message = typeof detail === 'string' ? detail : 'A requisição falhou.'
  return new ApiError('client', message, { status, details: detail, request })
}

export function networkError(request?: string, cause?: unknown): ApiError {
  const err = new ApiError('network', 'Sem conexão com a API. Verifique sua rede e tente novamente.', { status: null, request })
  if (cause !== undefined) (err as { cause?: unknown }).cause = cause
  return err
}

export function isApiError(value: unknown): value is ApiError {
  return value instanceof ApiError || (typeof value === 'object' && value !== null && (value as { name?: string }).name === 'ApiError')
}

/** Desembrulha o ApiError de wrappers (ex.: `createError` do Nuxt guarda o original em `cause`). */
export function unwrapApiError(value: unknown, depth = 0): ApiError | null {
  if (isApiError(value)) return value
  if (depth < 5 && typeof value === 'object' && value !== null && 'cause' in value) {
    return unwrapApiError((value as { cause?: unknown }).cause, depth + 1)
  }
  return null
}

/** Texto curto/mono para o detalhe do ErrorState. */
export function describeError(error: unknown): string | undefined {
  const err = unwrapApiError(error)
  if (!err) return undefined
  if (!err.request) return err.status ? `HTTP ${err.status}` : undefined
  return err.status ? `${err.request} · ${err.status}` : `${err.request} · rede`
}

/** Mensagem amigável (do ApiError) ou fallback. */
export function messageOf(error: unknown, fallback = 'A API não respondeu. Tente de novo em alguns segundos.'): string {
  return unwrapApiError(error)?.message ?? fallback
}
