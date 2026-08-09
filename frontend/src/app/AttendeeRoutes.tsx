import { RoleGate } from '../shared/RoleGate'
import { ReservationsPage } from './lazyPages'

export function ReservationsRoute() {
  return (
    <RoleGate role="attendee">
      <ReservationsPage />
    </RoleGate>
  )
}
