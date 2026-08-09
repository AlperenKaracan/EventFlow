import { createContext, useContext } from 'react'

export type FeedbackContextValue = {
  showSuccess: (message: string) => void
}

export const FeedbackContext = createContext<FeedbackContextValue | null>(null)

export function useFeedback() {
  const context = useContext(FeedbackContext)
  if (!context) {
    throw new Error('useFeedback must be used within FeedbackProvider')
  }
  return context
}
