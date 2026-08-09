import { render, screen } from '@testing-library/react'

import { App } from './App'

describe('App', () => {
  it('renders the foundation status accessibly', () => {
    render(<App />)

    expect(
      screen.getByRole('heading', { name: /etkinlik rezervasyonu/i }),
    ).toBeInTheDocument()
    expect(screen.getByRole('status')).toHaveTextContent('Frontend çalışıyor')
  })
})
