import { render, screen } from '@testing-library/react'
import { vi } from 'vitest'

import { AppProviders } from './AppProviders'
import { App } from './App'

vi.mock('../api/publicEvents', () => ({
  fetchPublicEvents: vi.fn().mockResolvedValue({
    items: [],
    nextCursor: null,
    hasMore: false,
  }),
  fetchPublicEvent: vi.fn(),
}))

describe('App', () => {
  it('renders the public events route accessibly', async () => {
    window.history.pushState({}, '', '/')
    render(
      <AppProviders>
        <App />
      </AppProviders>,
    )

    expect(
      await screen.findByRole('heading', { name: 'Yaklaşan etkinlikler' }),
    ).toBeInTheDocument()
  })
})
