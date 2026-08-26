import { describe, expect, it } from 'vitest'
import { mountSuspended } from '@nuxt/test-utils/runtime'
import SymbolSelector from '../../app/components/SymbolSelector.vue'
import type { SymbolRow } from '../../app/types/api'

/** A tabela `symbols` traz todo par USDT visto; só os `tracked` têm candles. */
const SYMBOLS: SymbolRow[] = [
  { symbol: 'BTCUSDT', tracked: true },
  { symbol: 'CTSIUSDT', tracked: false },
  { symbol: 'ETHUSDT', tracked: true },
  { symbol: 'CRVUSDT', tracked: false },
]

describe('SymbolSelector', () => {
  it('oferece só os ativos rastreados e informa a contagem certa', async () => {
    const wrapper = await mountSuspended(SymbolSelector, {
      props: { symbols: SYMBOLS, tickers: [], status: 'success', modelValue: 'BTCUSDT' },
    })
    const vm = wrapper.vm as unknown as { items: { symbol: string }[] }
    expect(vm.items.map(i => i.symbol)).toEqual(['BTCUSDT', 'ETHUSDT'])
    expect(wrapper.text()).toContain('BTCUSDT')
  })

  it('sem rastreados a lista fica vazia em vez de oferecer ativos sem candles', async () => {
    const wrapper = await mountSuspended(SymbolSelector, {
      props: { symbols: SYMBOLS.filter(s => !s.tracked), tickers: [], status: 'success', modelValue: null },
    })
    const vm = wrapper.vm as unknown as { items: { symbol: string }[] }
    expect(vm.items).toEqual([])
  })
})
