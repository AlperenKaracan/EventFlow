import { describe, expect, it } from 'vitest'

import { loginSchema, registerSchema } from './schemas'

describe('auth form schemas', () => {
  it('rejects invalid login fields', () => {
    const result = loginSchema.safeParse({ email: 'invalid', password: '' })

    expect(result.success).toBe(false)
  })

  it('matches backend registration limits and trims the full name', () => {
    const result = registerSchema.parse({
      email: 'person@example.com',
      fullName: '  Event Flow  ',
      password: 'long-password',
      role: 'organizer',
    })

    expect(result.fullName).toBe('Event Flow')
    expect(result.role).toBe('organizer')
  })

  it('rejects registration passwords shorter than 12 characters', () => {
    const result = registerSchema.safeParse({
      email: 'person@example.com',
      fullName: 'Event Flow',
      password: 'short',
      role: 'attendee',
    })

    expect(result.success).toBe(false)
  })
})
