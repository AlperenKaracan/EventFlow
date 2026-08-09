import { Alert, Snackbar } from '@mui/material'
import { type PropsWithChildren, useCallback, useMemo, useState } from 'react'

import { FeedbackContext } from './feedback'

export function FeedbackProvider({ children }: PropsWithChildren) {
  const [message, setMessage] = useState<string | null>(null)
  const showSuccess = useCallback((nextMessage: string) => {
    setMessage(nextMessage)
  }, [])
  const value = useMemo(() => ({ showSuccess }), [showSuccess])

  return (
    <FeedbackContext.Provider value={value}>
      {children}
      <Snackbar
        open={Boolean(message)}
        autoHideDuration={5000}
        onClose={() => setMessage(null)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          severity="success"
          variant="filled"
          onClose={() => setMessage(null)}
          sx={{ width: '100%', boxShadow: 4 }}
        >
          {message}
        </Alert>
      </Snackbar>
    </FeedbackContext.Provider>
  )
}
