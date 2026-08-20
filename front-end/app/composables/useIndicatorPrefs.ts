import { useLocalStorage } from '@vueuse/core'
import { DEFAULT_INDICATORS, INDICATOR_DEFS, STORAGE_KEYS, type IndicatorKey } from '~/utils/constants'

export type IndicatorPrefs = Record<IndicatorKey, boolean>

function sanitize(value: unknown): IndicatorPrefs {
  const out = { ...DEFAULT_INDICATORS }
  if (value && typeof value === 'object') {
    for (const def of INDICATOR_DEFS) {
      const v = (value as Record<string, unknown>)[def.key]
      if (typeof v === 'boolean') out[def.key] = v
    }
  }
  return out
}

/** Toggles de indicadores persistidos no navegador (`cf:indicators:v1`). */
export function useIndicatorPrefs() {
  const prefs = useLocalStorage<IndicatorPrefs>(STORAGE_KEYS.indicators, { ...DEFAULT_INDICATORS }, {
    mergeDefaults: true,
    serializer: {
      read: raw => sanitize(JSON.parse(raw)),
      write: value => JSON.stringify(value),
    },
  })

  const enabledCount = computed(() => Object.values(prefs.value).filter(Boolean).length)
  const enabledKeys = computed(() => INDICATOR_DEFS.filter(d => prefs.value[d.key]).map(d => d.key))

  function toggle(key: IndicatorKey, value?: boolean) {
    prefs.value = { ...prefs.value, [key]: value ?? !prefs.value[key] }
  }

  function restoreDefaults() {
    prefs.value = { ...DEFAULT_INDICATORS }
  }

  /** Limpa tudo e devolve um snapshot para "Desfazer" (ux-spec §11). */
  function clearAll(): IndicatorPrefs {
    const snapshot = { ...prefs.value }
    const cleared = Object.fromEntries(INDICATOR_DEFS.map(d => [d.key, false])) as IndicatorPrefs
    prefs.value = cleared
    return snapshot
  }

  function restore(snapshot: IndicatorPrefs) {
    prefs.value = sanitize(snapshot)
  }

  return { prefs, enabledCount, enabledKeys, toggle, restoreDefaults, clearAll, restore }
}
