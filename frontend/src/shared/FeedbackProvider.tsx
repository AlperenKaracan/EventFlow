import { Alert, Snackbar } from '@mui/material'
import {
  createContext,
  type PropsWithChildren,
  useCallback,
  useContext,
  useMemo,
  useState,
} from 'react'

type FeedbackContextValue = {
  showSuccess: (message: string) => void
}

const FeedbackContext = createContext<FeedbackContextValue | null>(null)

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

export function useFeedback() {
  const context = useContext(FeedbackContext)
  if (!context) {
    throw new Error('useFeedback must be used within FeedbackProvider')
  }
  return context
}
