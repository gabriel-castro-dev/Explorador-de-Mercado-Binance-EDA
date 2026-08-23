import createClient from 'openapi-fetch'
import type { Client, ClientPathsWithMethod, MaybeOptionalInit, MethodResponse } from 'openapi-fetch'
import type { paths } from '~/types/openapi'
import { networkError, normalizeApiError, type ApiError } from '~/utils/api-errors'

type HttpMethod = 'get' | 'put' | 'post'
type PathsWith<M extends HttpMethod> = ClientPathsWithMethod<Client<paths>, M>
type Init<M extends HttpMethod, P extends PathsWith<M>> = MaybeOptionalInit<paths[P], M>
type Data<M extends HttpMethod, P extends PathsWith<M>> = MethodResponse<Client<paths>, M, P>

export interface ApiClient {
  /** GET tipado: lança `ApiError` em qualquer não-2xx / falha de rede. */
  get: <P extends PathsWith<'get'>>(path: P, init?: Init<'get', P>) => Promise<Data<'get', P>>
  /** PUT tipado: mesma política de auth/erros do GET. */
  put: <P extends PathsWith<'put'>>(path: P, init: Init<'put', P>) => Promise<Data<'put', P>>
  /** POST tipado: mesma política de auth/erros do GET. */
  post: <P extends PathsWith<'post'>>(path: P, init?: Init<'post', P>) => Promise<Data<'post', P>>
}

interface SessionProvider {
  getAccessToken: () => Promise<string | null>
  /** Tenta renovar a sessão; devolve true se há sessão válida depois. */
  refresh: () => Promise<boolean>
  /** Sessão irrecuperável: desconecta e redireciona (ux-spec §3.7). */
  onExpired: () => Promise<void>
}

function describe(method: HttpMethod, path: string, init?: { params?: { path?: Record<string, unknown> } }): string {
  let p = path.replace('/api/v1', '')
  for (const [k, v] of Object.entries(init?.params?.path ?? {})) p = p.replace(`{${k}}`, String(v))
  return `${method.toUpperCase()} ${p}`
}

/** Núcleo sem Nuxt (testável): cliente + política de auth/erros. */
export function createApiClient(baseUrl: string, session: SessionProvider, fetchImpl?: typeof fetch): ApiClient {
  const raw = createClient<paths>({ baseUrl, fetch: fetchImpl })

  async function request(method: HttpMethod, path: string, init: object | undefined, token: string | null) {
    const headers: Record<string, string> = {}
    if (token) headers.Authorization = `Bearer ${token}`
    const merged = { ...(init ?? {}), headers }
    const fn = method === 'get' ? raw.GET : method === 'put' ? raw.PUT : raw.POST
    return fn(path as never, merged as never) as Promise<{ data?: unknown, error?: unknown, response: Response }>
  }

  let expiring: Promise<void> | null = null

  async function call(method: HttpMethod, path: string, init: object | undefined): Promise<unknown> {
    const label = describe(method, path, init as never)
    const isPublic = path === '/health'
    let token = isPublic ? null : await session.getAccessToken()

    let res: Awaited<ReturnType<typeof request>>
    try {
      res = await request(method, path, init, token)
    } catch (cause) {
      throw networkError(label, cause)
    }

    if (res.response.status === 401 && !isPublic) {
      const refreshed = await session.refresh()
      if (refreshed) {
        token = await session.getAccessToken()
        try {
          res = await request(method, path, init, token)
        } catch (cause) {
          throw networkError(label, cause)
        }
      }
      if (res.response.status === 401) {
        // Uma única expiração por vez, mesmo com N requisições em paralelo.
        expiring ??= session.onExpired().finally(() => {
          expiring = null
        })
        await expiring
        throw normalizeApiError(401, res.error, label)
      }
    }

    if (!res.response.ok) {
      const body = res.error ?? (await res.response.text().catch(() => undefined))
      throw normalizeApiError(res.response.status, body, label)
    }
    return res.data
  }

  return {
    get: (path, init) => call('get', path, init as object | undefined) as never,
    put: (path, init) => call('put', path, init as object | undefined) as never,
    post: (path, init) => call('post', path, init as object | undefined) as never,
  }
}

/** Cliente da API para o app: Bearer da sessão Supabase; 401 → refresh → retry → signOut + /login. */
export function useApi(): ApiClient {
  const nuxtApp = useNuxtApp()
  const cached = (nuxtApp as unknown as { _cfApi?: ApiClient })._cfApi
  if (cached) return cached

  const { public: { apiBase } } = useRuntimeConfig()
  const supabase = useSupabaseClient()
  const toast = useToast()

  const client = createApiClient(apiBase, {
    async getAccessToken() {
      const { data } = await supabase.auth.getSession()
      return data.session?.access_token ?? null
    },
    async refresh() {
      const { data, error } = await supabase.auth.refreshSession()
      return !error && !!data.session
    },
    async onExpired() {
      const route = useRoute()
      if (route.path !== '/login') {
        useSupabaseCookieRedirect().path.value = route.fullPath
      }
      await supabase.auth.signOut()
      clearNuxtData()
      toast.add({ title: 'Sessão expirada. Entre de novo para continuar.', color: 'neutral', icon: 'i-lucide-clock' })
      await navigateTo({ path: '/login', query: { reason: 'expired' } })
    },
  })

  ;(nuxtApp as unknown as { _cfApi?: ApiClient })._cfApi = client
  return client
}

export type { ApiError }
