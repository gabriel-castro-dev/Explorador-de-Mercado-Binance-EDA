// Aliases legíveis sobre os tipos GERADOS em openapi.d.ts (pnpm api:types). Nunca editar api.d.ts à mão.
import type { components } from './openapi'

export type Kline = components['schemas']['KlineOut']
export type FeatureRow = components['schemas']['FeatureRowOut']
export type Ticker24h = components['schemas']['Ticker24hOut']
export type SymbolRow = components['schemas']['SymbolOut']
export type Health = components['schemas']['HealthOut']
export type Timeframe = components['schemas']['Timeframe']
export type DailyReading = components['schemas']['DailyReadingOut']
export type ForecastPoint = components['schemas']['ForecastOut']
export type PreferencesIn = components['schemas']['PreferencesIn']
export type PreferencesOut = components['schemas']['PreferencesOut']
export type NotificationChannel = NonNullable<PreferencesIn['notifications']>['channel']

/** Chaves numéricas (indicadores) de uma linha de features — todas nullable (warm-up). */
export type FeatureKey = Exclude<keyof FeatureRow, 'symbol' | 'timestamp'>
