import type { PublicEventFilters } from '../../api/publicEvents'

export function validatePublicEventFilters(
  filters: PublicEventFilters,
): string | null {
  if (filters.dateFrom && filters.dateTo && filters.dateFrom > filters.dateTo) {
    return 'Başlangıç tarihi bitiş tarihinden sonra olamaz.'
  }
  return null
}
