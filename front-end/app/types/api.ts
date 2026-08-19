// Aliases legíveis sobre os tipos GERADOS em openapi.d.ts (pnpm api:types). Nunca editar api.d.ts à mão.
import type { components } from './openapi'

export type Kline = components['schemas']['KlineOut']
export type FeatureRow = components['schemas']['FeatureRowOut']
export type Ticker24h = components['schemas']['Ticker24hOut']
export type SymbolRow = components['schemas']['SymbolOut']
export type Health = components['schemas']['HealthOut']
export type Timeframe = components['schemas']['Timeframe']

/** Chaves numéricas (indicadores) de uma linha de features — todas nullable (warm-up). */
export type FeatureKey = Exclude<keyof FeatureRow, 'symbol' | 'timestamp'>
