import { describe, expect, it } from 'vitest'

import { getCategoryAccent } from './categoryAccent'

describe('getCategoryAccent', () => {
  it('assigns every seeded category a distinct accessible foreground', () => {
    const slugs = [
      'teknoloji',
      'muzik',
      'spor',
      'egitim',
      'sanat',
      'is-dunyasi',
    ]

    const foregrounds = slugs.map((slug) => getCategoryAccent(slug).foreground)

    expect(new Set(foregrounds).size).toBe(slugs.length)
  })

  it('uses a neutral fallback for categories added later', () => {
    expect(getCategoryAccent('gelecekteki-kategori')).toEqual({
      background: 'rgba(148, 163, 184, 0.14)',
      border: 'rgba(148, 163, 184, 0.48)',
      foreground: '#cbd5e1',
      glow: 'rgba(148, 163, 184, 0.16)',
    })
  })
})
