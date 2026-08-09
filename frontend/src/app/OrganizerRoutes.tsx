import {
  OrganizerAttendeesPage,
  OrganizerEventFormPage,
  OrganizerEventsPage,
} from './lazyPages'
import { RoleGate } from '../shared/RoleGate'

export function OrganizerEventsRoute() {
  return (
    <RoleGate role="organizer">
      <OrganizerEventsPage />
    </RoleGate>
  )
}

export function OrganizerEventCreateRoute() {
  return (
    <RoleGate role="organizer">
      <OrganizerEventFormPage />
    </RoleGate>
  )
}

export function OrganizerEventEditRoute({ eventId }: { eventId: string }) {
  return (
    <RoleGate role="organizer">
      <OrganizerEventFormPage eventId={eventId} />
    </RoleGate>
  )
}

export function OrganizerAttendeesRoute({ eventId }: { eventId: string }) {
  return (
    <RoleGate role="organizer">
      <OrganizerAttendeesPage eventId={eventId} />
    </RoleGate>
  )
}
