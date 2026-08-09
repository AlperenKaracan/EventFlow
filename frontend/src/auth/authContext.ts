import { createContext, useContext } from 'react'

import type {
  LoginRequest,
  RegisterRequest,
  UserResponse,
} from '../api/generated'
import type { SessionState } from './session'

export interface AuthContextValue {
  session: SessionState
  login: (credentials: LoginRequest) => Promise<UserResponse>
  logout: () => Promise<void>
  register: (input: RegisterRequest) => Promise<UserResponse>
}

export const AuthContext = createContext<AuthContextValue | null>(null)

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth, AuthProvider içinde kullanılmalıdır.')
  return context
}
