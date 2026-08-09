import { Link } from '@tanstack/react-router'
import {
  Box,
  Card,
  CardContent,
  Chip,
  Container,
  Typography,
} from '@mui/material'
import type { PropsWithChildren } from 'react'

export function AuthFormLayout({
  title,
  description,
  footer,
  children,
}: PropsWithChildren<{
  title: string
  description: string
  footer: 'login' | 'register'
}>) {
  return (
    <Container component="main" maxWidth="lg" sx={{ py: { xs: 3, md: 7 } }}>
      <Box
        sx={{
          alignItems: 'stretch',
          display: 'grid',
          gap: 3,
          gridTemplateColumns: {
            xs: '1fr',
            md: 'minmax(0, 1fr) minmax(420px, .8fr)',
          },
        }}
      >
        <Box
          sx={{
            background:
              'linear-gradient(145deg, #172554, #4f46e5 60%, #0f766e)',
            borderRadius: 4,
            color: 'common.white',
            display: { xs: 'none', md: 'flex' },
            flexDirection: 'column',
            justifyContent: 'space-between',
            minHeight: 600,
            overflow: 'hidden',
            p: 6,
            position: 'relative',
          }}
        >
          <Box sx={{ position: 'relative', zIndex: 1 }}>
            <Chip
              label="Etkinlikler, tek akışta"
              sx={{ bgcolor: 'rgba(255,255,255,.14)', color: 'white' }}
            />
            <Typography
              component="p"
              variant="h2"
              sx={{ mt: 3, maxWidth: 520 }}
            >
              Planla, paylaş ve topluluğunu büyüt.
            </Typography>
            <Typography
              sx={{ color: 'rgba(255,255,255,.75)', mt: 2, maxWidth: 480 }}
            >
              EventFlow; organizatörler ve katılımcılar için güvenli, yalın ve
              hızlı bir etkinlik deneyimi sunar.
            </Typography>
          </Box>
          <Typography
            sx={{ color: 'rgba(255,255,255,.7)', position: 'relative' }}
          >
            Güvenli rezervasyon · Şeffaf kontenjan · Kolay yönetim
          </Typography>
        </Box>
        <Card variant="outlined" sx={{ alignSelf: 'center', width: '100%' }}>
          <CardContent sx={{ p: { xs: 3, sm: 5 } }}>
            <Typography component="h1" variant="h2">
              {title}
            </Typography>
            <Typography color="text.secondary" sx={{ mt: 1, mb: 4 }}>
              {description}
            </Typography>
            {children}
            <Typography
              color="text.secondary"
              sx={{ mt: 3, textAlign: 'center' }}
            >
              {footer === 'login'
                ? 'Hesabınız yok mu? '
                : 'Zaten hesabınız var mı? '}
              <Link to={footer === 'login' ? '/register' : '/login'}>
                {footer === 'login' ? 'Kayıt olun' : 'Giriş yapın'}
              </Link>
            </Typography>
          </CardContent>
        </Card>
      </Box>
    </Container>
  )
}
