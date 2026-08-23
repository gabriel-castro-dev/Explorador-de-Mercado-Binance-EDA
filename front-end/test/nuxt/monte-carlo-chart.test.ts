import { describe, expect, it } from 'vitest'
import { mountSuspended } from '@nuxt/test-utils/runtime'
import MonteCarloChart from '../../app/components/forecast/MonteCarloChart.client.vue'
import type { MonteCarloSeries } from '../../app/types/forecast'

/**
 * Fixtures existem **apenas aqui**: a produção só desenha trajetórias reais
 * recebidas por props (Design.md §11.3).
 */
function fixture(): MonteCarloSeries {
  const observed = Array.from({ length: 20 }, (_, i) => ({
    time: 1_700_000_000 + i * 86_400,
    value: 100 + Math.sin(i / 3) * 4,
  }))
  const paths = [
    [102, 106, 112, 119],
    [99, 96, 92, 87],
    [100, 101, 103, 104],
    [101, 100, 102, 101],
  ]
  return {
    symbol: 'BTCUSDT',
    horizonDays: 30,
    observed,
    stepSeconds: 86_400,
    paths,
    simulatedCount: 1000,
  }
}

describe('MonteCarloChart', () => {
  it('sem trajetórias mostra o estado honesto e não desenha canvas', async () => {
    const wrapper = await mountSuspended(MonteCarloChart, { props: { series: null } })
    expect(wrapper.text()).toContain('O modelo ainda não publicou previsões para este ativo.')
    expect(wrapper.find('canvas').exists()).toBe(false)
  })

  it('com trajetórias reais desenha o canvas e descreve a simulação', async () => {
    const wrapper = await mountSuspended(MonteCarloChart, { props: { series: fixture() } })
    const canvas = wrapper.find('canvas')
    expect(canvas.exists()).toBe(true)
    expect(canvas.attributes('role')).toBe('img')
    expect(canvas.attributes('aria-label')).toContain('BTCUSDT')
    expect(canvas.attributes('aria-label')).toContain('1.000 trajetórias simuladas')
    // touch-action: none só no canvas (Design.md §14.2)
    expect(canvas.attributes('style')).toContain('touch-action: none')
  })

  it('informa a quantidade realmente simulada, não a desenhada', async () => {
    const wrapper = await mountSuspended(MonteCarloChart, { props: { series: fixture() } })
    expect(wrapper.text()).toContain('1.000 trajetórias simuladas')
  })

  it('oferece a legenda melhor/base/pior e a tabela alternativa', async () => {
    const wrapper = await mountSuspended(MonteCarloChart, { props: { series: fixture() } })
    const text = wrapper.text()
    expect(text).toContain('Melhor cenário')
    expect(text).toContain('Cenário base')
    expect(text).toContain('Pior cenário')
    expect(text).toContain('Ver como tabela')
  })

  it('expõe controles de pan e zoom com rótulo acessível', async () => {
    const wrapper = await mountSuspended(MonteCarloChart, { props: { series: fixture() } })
    const labels = wrapper.findAll('button').map(b => b.attributes('aria-label')).filter(Boolean)
    expect(labels).toEqual(expect.arrayContaining([
      'Deslocar para trás',
      'Deslocar para frente',
      'Afastar',
      'Aproximar',
      'Enquadrar tudo',
    ]))
  })
})
