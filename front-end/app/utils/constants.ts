import type { FeatureKey, Timeframe } from '~/types/api'

export const TIMEFRAMES: readonly Timeframe[] = ['15m', '1h', '1d'] as const

export function isTimeframe(value: unknown): value is Timeframe {
  return typeof value === 'string' && (TIMEFRAMES as readonly string[]).includes(value)
}

export const DEFAULT_TIMEFRAME: Timeframe = '1h'

/** Janela de leitura por timeframe: cobre toda a retenção (15m 7d, 1h 30d); 1d é o teto da API. */
export const LIMIT_BY_TF: Record<Timeframe, number> = {
  '15m': 672,
  '1h': 720,
  '1d': 1000,
}

export const TIMEFRAME_META: Record<Timeframe, { label: string, subtitle: string, retention: string, seconds: number }> = {
  '15m': { label: '15m', subtitle: '15m · últimos 7 dias', retention: 'retenção 7 dias', seconds: 15 * 60 },
  '1h': { label: '1h', subtitle: '1h · últimos 30 dias', retention: 'retenção 30 dias', seconds: 60 * 60 },
  '1d': { label: '1d', subtitle: '1d · histórico completo', retention: 'histórico completo', seconds: 24 * 60 * 60 },
}

/** Limiar de "dados velhos" (ux-spec §6), em horas. */
export const STALE_AFTER_HOURS = { klines: 26, tickers: 2 } as const

/** Velas 1d: a última vela (aberta) tem open_time de até ~48 h → limiar maior. */
export const STALE_AFTER_HOURS_BY_TF: Record<Timeframe, number> = { '15m': 26, '1h': 26, '1d': 50 }

export type LineStyleName = 'solid' | 'dashed' | 'dotted'
export type IndicatorPane = 'price' | 'volume' | 'rsi' | 'macd'

export interface IndicatorDef {
  key: IndicatorKey
  label: string
  /** Grupo do painel de toggles. */
  group: 'price' | 'below'
  pane: IndicatorPane
  /** Cor única — dark-only (Design.md §2.4). */
  color: string
  lineStyle: LineStyleName
  /** Espessura em px; a escala crescente por período é canal secundário obrigatório (audit.md). */
  lineWidth: number
  /** Campos da API que compõem a série. */
  fields: readonly FeatureKey[]
  /** Janela de cálculo em velas (para a nota de warm-up). */
  window?: number
  /** Descrição curta para tooltip/título. */
  title?: string
}

export type IndicatorKey
  = | 'sma20' | 'sma50' | 'sma200' | 'ema12' | 'ema26' | 'bb' | 'volume' | 'rsi' | 'macd'

/**
 * Família azul/gelo (Design.md §2.4). O par SMA 20×50 não passa o piso de distinção por
 * cor do validador (ΔE 9.9 < 15, audit.md) — a mitigação obrigatória é: espessura crescente
 * por período, SMA contínua × EMA tracejada × BB pontilhada e legenda com valores sempre visível.
 * Recomendação de uso: no máx. 2–3 overlays ligados (padrão: SMA 20 + SMA 50).
 */
export const INDICATOR_DEFS: readonly IndicatorDef[] = [
  { key: 'sma20', label: 'SMA 20', group: 'price', pane: 'price', color: '#4f8ff7', lineStyle: 'solid', lineWidth: 1.2, fields: ['sma_20'], window: 20 },
  { key: 'sma50', label: 'SMA 50', group: 'price', pane: 'price', color: '#2596be', lineStyle: 'solid', lineWidth: 1.8, fields: ['sma_50'], window: 50 },
  { key: 'sma200', label: 'SMA 200', group: 'price', pane: 'price', color: '#c8d9ef', lineStyle: 'solid', lineWidth: 2.2, fields: ['sma_200'], window: 200, title: 'SMA 200 só existe a partir da 200ª vela' },
  { key: 'ema12', label: 'EMA 12', group: 'price', pane: 'price', color: '#8ab8ff', lineStyle: 'dashed', lineWidth: 1.2, fields: ['ema_12'], window: 12 },
  { key: 'ema26', label: 'EMA 26', group: 'price', pane: 'price', color: '#2f5fd0', lineStyle: 'dashed', lineWidth: 1.8, fields: ['ema_26'], window: 26 },
  { key: 'bb', label: 'Bollinger 20·2', group: 'price', pane: 'price', color: 'rgba(200,217,239,.55)', lineStyle: 'dotted', lineWidth: 1, fields: ['bb_upper', 'bb_middle', 'bb_lower'], window: 20 },
  { key: 'volume', label: 'Volume', group: 'price', pane: 'volume', color: 'rgba(219,231,245,.28)', lineStyle: 'solid', lineWidth: 1, fields: [] },
  { key: 'rsi', label: 'RSI 14', group: 'below', pane: 'rsi', color: '#4f8ff7', lineStyle: 'solid', lineWidth: 1, fields: ['rsi_14'], window: 14 },
  { key: 'macd', label: 'MACD 12·26·9', group: 'below', pane: 'macd', color: '#4f8ff7', lineStyle: 'solid', lineWidth: 1, fields: ['macd', 'macd_signal', 'macd_histogram'], window: 34 },
] as const

export const INDICATOR_BY_KEY: Record<IndicatorKey, IndicatorDef> = Object.fromEntries(
  INDICATOR_DEFS.map(d => [d.key, d]),
) as Record<IndicatorKey, IndicatorDef>

/** Cor do sinal do MACD (slot 2): gelo, contra a linha azul. */
export const MACD_SIGNAL_COLOR = '#dbe7f5'

/**
 * Velas gelo × vermelho (Design.md §2.4): alta vazada por padrão (corpo gelo a 10 %,
 * contorno gelo — a identidade da logo), baixa preenchida. `upBody` é o corpo da vazada;
 * `up` cheio é a opção de acessibilidade "Velas de alta preenchidas".
 */
export const CANDLE_COLORS = {
  up: '#dbe7f5',
  upBody: 'rgba(219,231,245,.10)',
  down: '#e5484d',
  flat: '#66788f',
  upSoft: 'rgba(219,231,245,.28)',
  downSoft: 'rgba(229,72,77,.30)',
  upHist: 'rgba(219,231,245,.45)',
  downHist: 'rgba(229,72,77,.45)',
} as const

/** Cenários do modelo (melhor/esperada/pior) — tracejadas depois da linha de corte. */
export const SCENARIO_COLORS = {
  best: '#dbe7f5',
  expected: '#5fc4ff',
  worst: '#e5484d',
  band: 'rgba(95,196,255,.08)',
} as const

export const DEFAULT_INDICATORS: Record<IndicatorKey, boolean> = {
  sma20: true,
  sma50: true,
  sma200: false,
  ema12: false,
  ema26: false,
  bb: false,
  volume: true,
  rsi: true,
  macd: true,
}

export const STORAGE_KEYS = {
  indicators: 'cf:indicators:v1',
  onboarded: 'cf:onboarded:v1',
  hollowCandles: 'cf:hollow-candles:v1',
  macdMobileDismissed: 'cf:macd-mobile:v1',
  scenarios: 'cf:scenarios:v1',
  lastSeenAt: 'cf:last-seen-at:v1',
  lastSymbol: 'cf:last-symbol:v1',
} as const

/** Nomes legíveis dos pares mais comuns (fallback: só o símbolo). */
export const SYMBOL_NAMES: Record<string, string> = {
  BTCUSDT: 'Bitcoin / Tether',
  ETHUSDT: 'Ethereum / Tether',
  SOLUSDT: 'Solana / Tether',
  XRPUSDT: 'XRP / Tether',
  BNBUSDT: 'BNB / Tether',
  DOGEUSDT: 'Dogecoin / Tether',
  ADAUSDT: 'Cardano / Tether',
  LINKUSDT: 'Chainlink / Tether',
  PEPEUSDT: 'Pepe / Tether',
  AVAXUSDT: 'Avalanche / Tether',
  TRXUSDT: 'TRON / Tether',
  SUIUSDT: 'Sui / Tether',
  LTCUSDT: 'Litecoin / Tether',
  DOTUSDT: 'Polkadot / Tether',
  BCHUSDT: 'Bitcoin Cash / Tether',
  NEARUSDT: 'NEAR / Tether',
  SHIBUSDT: 'Shiba Inu / Tether',
  TONUSDT: 'Toncoin / Tether',
  UNIUSDT: 'Uniswap / Tether',
  AAVEUSDT: 'Aave / Tether',
  HBARUSDT: 'Hedera / Tether',
  XLMUSDT: 'Stellar / Tether',
  WLDUSDT: 'Worldcoin / Tether',
  ENAUSDT: 'Ethena / Tether',
  FETUSDT: 'Fetch.ai / Tether',
}

export function symbolName(symbol: string): string | undefined {
  return SYMBOL_NAMES[symbol]
}

/** Ativo base de um par USDT ("BTCUSDT" → "BTC"). */
export function baseAsset(symbol: string): string {
  return symbol.endsWith('USDT') ? symbol.slice(0, -4) : symbol
}
