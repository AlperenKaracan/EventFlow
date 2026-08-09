import { type PropsWithChildren, useEffect, useSyncExternalStore } from 'react'

import { AuthContext } from './authContext'
import {
  bootstrapSession,
  getSessionSnapshot,
  login,
  logout,
  registerAndLogin,
  subscribeToSession,
} from './session'

export function AuthProvider({ children }: PropsWithChildren) {
  const session = useSyncExternalStore(
    subscribeToSession,
    getSessionSnapshot,
    getSessionSnapshot,
  )

  useEffect(() => {
    void bootstrapSession()
  }, [])

  return (
    <AuthContext.Provider
      value={{ session, login, logout, register: registerAndLogin }}
    >
      {children}
    </AuthContext.Provider>
  )
}
