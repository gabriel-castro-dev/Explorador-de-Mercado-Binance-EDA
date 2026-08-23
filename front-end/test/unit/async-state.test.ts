import { describe, expect, it } from 'vitest'
import { asyncView, isRefreshing } from '../../app/utils/async-state'

describe('asyncView', () => {
  it('erro sem dado vira error', () => {
    expect(asyncView('error', false)).toBe('error')
  })

  it('erro com dado anterior continua ready', () => {
    expect(asyncView('error', true)).toBe('ready')
  })

  it('pending com dado anterior continua ready (sem flash)', () => {
    expect(asyncView('pending', true)).toBe('ready')
  })

  it('pending sem dado vira loading', () => {
    expect(asyncView('pending', false)).toBe('loading')
  })

  it('sucesso sem linhas vira empty', () => {
    expect(asyncView('success', false)).toBe('empty')
  })

  it('idle sem dado permanece idle', () => {
    expect(asyncView('idle', false)).toBe('idle')
  })
})

describe('isRefreshing', () => {
  it('só é verdadeiro recarregando por cima de dado visível', () => {
    expect(isRefreshing('pending', true)).toBe(true)
    expect(isRefreshing('pending', false)).toBe(false)
    expect(isRefreshing('success', true)).toBe(false)
  })
})
