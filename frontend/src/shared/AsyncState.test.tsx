import { fireEvent, render, screen } from '@testing-library/react'
import { vi } from 'vitest'

import { ApiError } from '../api/errors'
import { ErrorState } from './AsyncState'

describe('ErrorState', () => {
  it('maps known errors to actionable copy without exposing request IDs', () => {
    render(
      <ErrorState
        error={
          new ApiError('Etkinlik kapasitesi dolu.', {
            code: 'EVENT_FULL',
            requestId: 'internal-request-id',
          })
        }
      />,
    )

    expect(screen.getByText('Etkinlikte yer kalmadı')).toBeInTheDocument()
    expect(
      screen.getByText(/başka bir etkinlik seçebilirsiniz/),
    ).toBeInTheDocument()
    expect(screen.queryByText(/internal-request-id/)).not.toBeInTheDocument()
  })

  it('keeps retry available for recoverable failures', () => {
    const retry = vi.fn()
    render(<ErrorState error={new Error('network')} onRetry={retry} />)

    fireEvent.click(screen.getByRole('button', { name: 'Tekrar dene' }))
    expect(retry).toHaveBeenCalledOnce()
  })
})
