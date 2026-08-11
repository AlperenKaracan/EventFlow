import { useCallback, useState } from 'react'

export interface CursorPagerState {
  cursor: string | null
  page: number
  canGoBack: boolean
  goBack: () => void
  goForward: (nextCursor: string) => void
  reset: () => void
}

export function useCursorPager(): CursorPagerState {
  const [cursor, setCursor] = useState<string | null>(null)
  const [history, setHistory] = useState<Array<string | null>>([])

  const goForward = useCallback(
    (nextCursor: string) => {
      setHistory((previous) => [...previous, cursor])
      setCursor(nextCursor)
    },
    [cursor],
  )

  const goBack = useCallback(() => {
    setHistory((previous) => {
      const priorCursor = previous.at(-1)
      setCursor(priorCursor ?? null)
      return previous.slice(0, -1)
    })
  }, [])

  const reset = useCallback(() => {
    setCursor(null)
    setHistory([])
  }, [])

  return {
    cursor,
    page: history.length + 1,
    canGoBack: history.length > 0,
    goBack,
    goForward,
    reset,
  }
}
