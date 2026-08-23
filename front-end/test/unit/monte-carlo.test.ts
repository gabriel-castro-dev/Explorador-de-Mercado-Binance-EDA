import { describe, expect, it } from 'vitest'
import {
  quantile,
  quantileBand,
  sampleIndices,
  selectHighlighted,
  terminalValue,
  valueExtent,
} from '../../app/utils/monte-carlo'

describe('terminalValue', () => {
  it('devolve o último valor', () => {
    expect(terminalValue([1, 2, 3])).toBe(3)
  })

  it('devolve null para trajetória vazia', () => {
    expect(terminalValue([])).toBeNull()
  })
})

describe('selectHighlighted', () => {
  const paths = [
    [100, 104, 108], // maior terminal
    [100, 99, 96], // menor terminal
    [100, 101, 102], // mediana terminal
  ]

  it('escolhe maior, menor e mediana terminal entre trajetórias reais', () => {
    expect(selectHighlighted(paths)).toEqual({ best: 0, worst: 1, base: 2 })
  })

  it('respeita a classificação da API quando ela existe', () => {
    expect(selectHighlighted(paths, { best: 2, base: 0, worst: 1 })).toEqual({ best: 2, base: 0, worst: 1 })
  })

  it('ignora classificação fora do intervalo e volta à seleção por terminal', () => {
    expect(selectHighlighted(paths, { best: 99 })).toEqual({ best: 0, worst: 1, base: 2 })
  })

  it('devolve null sem trajetórias utilizáveis', () => {
    expect(selectHighlighted([])).toBeNull()
    expect(selectHighlighted([[]])).toBeNull()
  })

  it('nunca inventa índices: todos apontam para trajetórias recebidas', () => {
    const picked = selectHighlighted(paths)
    expect(picked).not.toBeNull()
    for (const index of Object.values(picked!)) {
      expect(paths[index]).toBeDefined()
    }
  })
})

describe('quantileBand', () => {
  it('nasce estreita na linha de corte e abre com o horizonte', () => {
    const band = quantileBand([
      [100, 102, 110],
      [100, 98, 90],
      [100, 100, 100],
    ], 0, 1)
    expect(band.low[0]).toBe(100)
    expect(band.high[0]).toBe(100)
    expect(band.high[2]! - band.low[2]!).toBeGreaterThan(band.high[1]! - band.low[1]!)
  })

  it('cobre o horizonte mais longo e ignora trajetórias curtas nos passos que faltam', () => {
    const band = quantileBand([[100, 110, 120], [100, 90]], 0, 1)
    expect(band.low).toHaveLength(3)
    // No passo 2 só a trajetória longa existe: a faixa colapsa nela, não em zero.
    expect(band.low[2]).toBe(120)
    expect(band.high[2]).toBe(120)
  })
})

describe('quantile', () => {
  it('interpola linearmente', () => {
    expect(quantile([0, 10], 0.5)).toBe(5)
    expect(quantile([0, 10, 20], 0)).toBe(0)
    expect(quantile([0, 10, 20], 1)).toBe(20)
  })
})

describe('sampleIndices', () => {
  it('devolve tudo quando cabe no teto', () => {
    expect(sampleIndices(3, 10)).toEqual([0, 1, 2])
  })

  it('amostra de forma determinística e preserva a ordem', () => {
    const first = sampleIndices(1000, 50)
    expect(first).toEqual(sampleIndices(1000, 50))
    expect([...first].sort((a, b) => a - b)).toEqual(first)
  })

  it('mantém os índices destacados na amostra', () => {
    const picked = sampleIndices(1000, 20, [7, 999])
    expect(picked).toContain(7)
    expect(picked).toContain(999)
  })
})

describe('valueExtent', () => {
  it('adiciona folga relativa', () => {
    const extent = valueExtent([10, 20], 0.1)
    expect(extent).toEqual({ min: 9, max: 21 })
  })

  it('abre uma faixa mínima para série constante', () => {
    const extent = valueExtent([5, 5])
    expect(extent!.min).toBeLessThan(5)
    expect(extent!.max).toBeGreaterThan(5)
  })

  it('devolve null sem valores finitos', () => {
    expect(valueExtent([Number.NaN])).toBeNull()
  })
})
