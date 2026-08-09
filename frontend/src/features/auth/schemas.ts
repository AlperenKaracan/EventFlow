import { z } from 'zod'

export const loginSchema = z.object({
  email: z.email('Geçerli bir e-posta adresi girin.'),
  password: z
    .string()
    .min(1, 'Şifrenizi girin.')
    .max(128, 'Şifre en fazla 128 karakter olabilir.'),
})

export const registerSchema = z.object({
  fullName: z
    .string()
    .trim()
    .min(1, 'Ad soyad alanı zorunludur.')
    .max(120, 'Ad soyad en fazla 120 karakter olabilir.'),
  email: z.email('Geçerli bir e-posta adresi girin.'),
  password: z
    .string()
    .min(12, 'Şifre en az 12 karakter olmalıdır.')
    .max(128, 'Şifre en fazla 128 karakter olabilir.'),
  role: z.enum(['attendee', 'organizer']),
})

export type LoginFormValues = z.infer<typeof loginSchema>
export type RegisterFormValues = z.infer<typeof registerSchema>
