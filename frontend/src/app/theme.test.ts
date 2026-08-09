import { describe, expect, it } from 'vitest'

import { theme } from './theme'

describe('EventFlow theme', () => {
  it('uses one dark color scheme for the whole application', () => {
    expect(theme.palette.mode).toBe('dark')
    expect(theme.palette.background.default).toBe('#080b11')
    expect(theme.palette.background.paper).toBe('#111722')
  })
})
