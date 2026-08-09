import { z } from 'zod'

export const eventFormSchema = z.object({
  categoryId: z.string().uuid('Bir kategori seçin.'),
  title: z.string().trim().min(1, 'Başlık zorunludur.').max(160),
  description: z.string().max(5000),
  location: z.string().trim().min(1, 'Konum zorunludur.').max(255),
  startsAt: z.string().min(1, 'Başlangıç zamanı zorunludur.'),
  timezone: z.string().trim().min(1, 'Saat dilimi zorunludur.').max(64),
  capacity: z.coerce.number().int().positive('Kapasite 0’dan büyük olmalıdır.'),
})

export type EventFormValues = z.infer<typeof eventFormSchema>
export type EventFormInput = z.input<typeof eventFormSchema>
