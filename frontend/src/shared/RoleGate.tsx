import { Navigate } from '@tanstack/react-router'
import type { PropsWithChildren } from 'react'

import type { RegistrationRole } from '../api/generated'
import { useAuth } from '../auth/authContext'
import { LoadingState } from './AsyncState'
import { ForbiddenPage } from './StatusPages'

export function RoleGate({
  role,
  children,
}: PropsWithChildren<{ role: RegistrationRole }>) {
  const { session } = useAuth()

  if (session.status === 'bootstrapping')
    return <LoadingState label="Oturum doğrulanıyor" />
  if (session.status === 'anonymous') return <Navigate to="/login" replace />
  if (session.user.role !== role) return <ForbiddenPage />
  return children
}
