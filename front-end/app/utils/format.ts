/** Formatação pt-BR (números) e UTC (horários). Tudo determinístico e testável em Node. */

const MONTHS_PT = ['jan', 'fev', 'mar', 'abr', 'mai', 'jun', 'jul', 'ago', 'set', 'out', 'nov', 'dez']

export const EM_DASH = '—'

export function toDate(value: string | number | Date): Date {
  return value instanceof Date ? value : new Date(value)
}

function pad2(n: number): string {
  return n < 10 ? `0${n}` : String(n)
}

/** `19 ago 00:00` (UTC, sem sufixo) — usado em eixos/legenda. */
export function formatUtcShort(value: string | number | Date, opts: { withTime?: boolean, withYear?: boolean } = {}): string {
  const d = toDate(value)
  if (Number.isNaN(d.getTime())) return EM_DASH
  const { withTime = true, withYear = false } = opts
  const day = d.getUTCDate()
  const month = MONTHS_PT[d.getUTCMonth()]
  let out = `${day} ${month}`
  if (withYear) out += ` ${d.getUTCFullYear()}`
  if (withTime) out += ` ${pad2(d.getUTCHours())}:${pad2(d.getUTCMinutes())}`
  return out
}

/** `19 ago 00:00 UTC` — selo de snapshot, cabeçalhos. */
export function formatUtc(value: string | number | Date, opts: { withTime?: boolean, withYear?: boolean } = {}): string {
  const s = formatUtcShort(value, opts)
  return s === EM_DASH ? s : `${s} UTC`
}

/** `há 12 min` · `há 6 h` · `há 31 h` · `há 3 d` (ux-spec §6). */
export function formatAgo(value: string | number | Date, now: Date = new Date()): string {
  const d = toDate(value)
  if (Number.isNaN(d.getTime())) return EM_DASH
  const diffMs = Math.max(0, now.getTime() - d.getTime())
  const minutes = Math.floor(diffMs / 60_000)
  if (minutes < 1) return 'agora'
  if (minutes < 60) return `há ${minutes} min`
  const hours = Math.floor(minutes / 60)
  if (hours < 48) return `há ${hours} h`
  return `há ${Math.floor(hours / 24)} d`
}

export function hoursSince(value: string | number | Date, now: Date = new Date()): number {
  const d = toDate(value)
  if (Number.isNaN(d.getTime())) return Number.POSITIVE_INFINITY
  return (now.getTime() - d.getTime()) / 3_600_000
}

/** Casas decimais adequadas à magnitude de um preço (113.512,3 · 0,2310 · 0,00001234). */
export function priceDecimals(value: number): number {
  const abs = Math.abs(value)
  if (abs >= 1000) return 1
  if (abs >= 100) return 2
  if (abs >= 1) return 3
  if (abs >= 0.01) return 4
  if (abs >= 0.0001) return 6
  return 8
}

export function formatNumber(value: number | null | undefined, decimals = 2, opts: { sign?: boolean } = {}): string {
  if (value === null || value === undefined || Number.isNaN(value)) return EM_DASH
  const fixed = Math.abs(value).toFixed(decimals)
  const [intPart = '0', fracPart] = fixed.split('.')
  const grouped = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, '.')
  const body = fracPart ? `${grouped},${fracPart}` : grouped
  if (value < 0) return `−${body}`
  if (opts.sign && value > 0) return `+${body}`
  return body
}

export function formatPrice(value: number | null | undefined, opts: { sign?: boolean } = {}): string {
  if (value === null || value === undefined || Number.isNaN(value)) return EM_DASH
  return formatNumber(value, priceDecimals(value), opts)
}

/** Variação absoluta com as casas decimais do preço de referência (ex.: `+901,0` para BTC, `0,0000` para DOGE). */
export function formatChange(change: number | null | undefined, referencePrice: number | null | undefined): string {
  if (change === null || change === undefined || Number.isNaN(change)) return EM_DASH
  const ref = referencePrice ?? change
  return formatNumber(change, priceDecimals(ref === 0 ? 1 : ref), { sign: true })
}

/** `+1,84 %` · `−0,62 %` · `+0,00 %`. */
export function formatPercent(value: number | null | undefined, decimals = 2): string {
  if (value === null || value === undefined || Number.isNaN(value)) return EM_DASH
  const body = formatNumber(value, decimals, { sign: true })
  // "+0,00 %" (sem seta) é o estado "sem variação"; "—" fica reservado a campo nulo.
  return `${value === 0 ? `+${body}` : body} %`
}

/** `4,33 bi` · `896 mi` · `38.412` — volumes grandes com sufixo pt-BR. */
export function formatCompact(value: number | null | undefined, decimals = 2): string {
  if (value === null || value === undefined || Number.isNaN(value)) return EM_DASH
  const abs = Math.abs(value)
  if (abs >= 1e9) return `${formatNumber(value / 1e9, decimals)} bi`
  if (abs >= 1e6) return `${formatNumber(value / 1e6, decimals)} mi`
  if (abs >= 1e4) return formatNumber(value, 0)
  return formatNumber(value, abs >= 100 ? 0 : 1)
}

export type Tone = 'up' | 'down' | 'flat'

export function toneOf(value: number | null | undefined): Tone | null {
  if (value === null || value === undefined || Number.isNaN(value)) return null
  if (value > 0) return 'up'
  if (value < 0) return 'down'
  return 'flat'
}

/** Seta de codificação secundária (nunca só cor): ▲ alta · ▼ baixa · '' sem variação. */
export function arrowOf(value: number | null | undefined): string {
  const tone = toneOf(value)
  if (tone === 'up') return '▲'
  if (tone === 'down') return '▼'
  return ''
}
