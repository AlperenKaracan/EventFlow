import { QueryClientProvider } from '@tanstack/react-query'
import { CssBaseline, ThemeProvider } from '@mui/material'
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider'
import { AdapterDayjs } from '@mui/x-date-pickers/AdapterDayjs'
import 'dayjs/locale/tr'
import type { PropsWithChildren } from 'react'

import { AuthProvider } from '../auth/AuthProvider'
import { FeedbackProvider } from '../shared/FeedbackProvider'
import { queryClient } from './queryClient'
import { theme } from './theme'

export function AppProviders({ children }: PropsWithChildren) {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <LocalizationProvider dateAdapter={AdapterDayjs} adapterLocale="tr">
        <QueryClientProvider client={queryClient}>
          <AuthProvider>
            <FeedbackProvider>{children}</FeedbackProvider>
          </AuthProvider>
        </QueryClientProvider>
      </LocalizationProvider>
    </ThemeProvider>
  )
}
