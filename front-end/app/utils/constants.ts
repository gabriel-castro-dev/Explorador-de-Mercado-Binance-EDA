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
  /** Cor por modo (tokens.md §2). */
  color: { light: string, dark: string }
  lineStyle: LineStyleName
  lineWidth: 1 | 2 | 3 | 4
  /** Campos da API que compõem a série. */
  fields: readonly FeatureKey[]
  /** Janela de cálculo em velas (para a nota de warm-up). */
  window?: number
  /** Descrição curta para tooltip/título. */
  title?: string
}

export type IndicatorKey
  = | 'sma20' | 'sma50' | 'sma200' | 'ema12' | 'ema26' | 'bb' | 'volume' | 'rsi' | 'macd'

export const INDICATOR_DEFS: readonly IndicatorDef[] = [
  { key: 'sma20', label: 'SMA 20', group: 'price', pane: 'price', color: { light: '#2a78d6', dark: '#3987e5' }, lineStyle: 'solid', lineWidth: 1, fields: ['sma_20'], window: 20 },
  { key: 'sma50', label: 'SMA 50', group: 'price', pane: 'price', color: { light: '#eb6834', dark: '#d95926' }, lineStyle: 'solid', lineWidth: 2, fields: ['sma_50'], window: 50 },
  { key: 'sma200', label: 'SMA 200', group: 'price', pane: 'price', color: { light: '#4a3aa7', dark: '#9085e9' }, lineStyle: 'solid', lineWidth: 2, fields: ['sma_200'], window: 200, title: 'SMA 200 só existe a partir da 200ª vela' },
  { key: 'ema12', label: 'EMA 12', group: 'price', pane: 'price', color: { light: '#eda100', dark: '#c98500' }, lineStyle: 'dashed', lineWidth: 1, fields: ['ema_12'], window: 12 },
  { key: 'ema26', label: 'EMA 26', group: 'price', pane: 'price', color: { light: '#e87ba4', dark: '#d55181' }, lineStyle: 'dashed', lineWidth: 2, fields: ['ema_26'], window: 26 },
  { key: 'bb', label: 'Bollinger 20·2', group: 'price', pane: 'price', color: { light: '#6b7280', dark: '#9ca3af' }, lineStyle: 'dotted', lineWidth: 1, fields: ['bb_upper', 'bb_middle', 'bb_lower'], window: 20 },
  { key: 'volume', label: 'Volume', group: 'price', pane: 'volume', color: { light: '#8b8b94', dark: '#71717a' }, lineStyle: 'solid', lineWidth: 1, fields: [] },
  { key: 'rsi', label: 'RSI 14', group: 'below', pane: 'rsi', color: { light: '#4f46e5', dark: '#818cf8' }, lineStyle: 'solid', lineWidth: 1, fields: ['rsi_14'], window: 14 },
  { key: 'macd', label: 'MACD 12·26·9', group: 'below', pane: 'macd', color: { light: '#2a78d6', dark: '#3987e5' }, lineStyle: 'solid', lineWidth: 1, fields: ['macd', 'macd_signal', 'macd_histogram'], window: 34 },
] as const

export const INDICATOR_BY_KEY: Record<IndicatorKey, IndicatorDef> = Object.fromEntries(
  INDICATOR_DEFS.map(d => [d.key, d]),
) as Record<IndicatorKey, IndicatorDef>

/** Cor do sinal do MACD (slot 2) e do histograma (alta/baixa a 60 %). */
export const MACD_SIGNAL_COLOR = { light: '#eb6834', dark: '#d95926' } as const

export const CANDLE_COLORS = {
  light: { up: '#0f9d58', down: '#d93025', flat: '#8b8b94', upSoft: 'rgba(15,157,88,.35)', downSoft: 'rgba(217,48,37,.35)', upHist: 'rgba(15,157,88,.6)', downHist: 'rgba(217,48,37,.6)' },
  dark: { up: '#26a69a', down: '#ef5350', flat: '#71717a', upSoft: 'rgba(38,166,154,.35)', downSoft: 'rgba(239,83,80,.35)', upHist: 'rgba(38,166,154,.6)', downHist: 'rgba(239,83,80,.6)' },
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
