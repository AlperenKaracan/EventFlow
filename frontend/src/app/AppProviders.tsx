import { QueryClientProvider } from '@tanstack/react-query'
import { CssBaseline, ThemeProvider } from '@mui/material'
import type { PropsWithChildren } from 'react'

import { AuthProvider } from '../auth/AuthProvider'
import { queryClient } from './queryClient'
import { theme } from './theme'

export function AppProviders({ children }: PropsWithChildren) {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <QueryClientProvider client={queryClient}>
        <AuthProvider>{children}</AuthProvider>
      </QueryClientProvider>
    </ThemeProvider>
  )
}
