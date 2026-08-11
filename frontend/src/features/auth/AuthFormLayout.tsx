import { Link } from '@tanstack/react-router'
import { Box, Container, Stack, Typography } from '@mui/material'
import type { PropsWithChildren } from 'react'

import { designTokens } from '../../app/theme'
import { Surface } from '../../shared/ui/Surface'

const benefits = [
  'Rezervasyonlarını tek yerden yönet',
  'Etkinlik saatlerini kendi saat diliminde gör',
  'Güvenli ve hızlı bir etkinlik deneyimi yaşa',
]

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
    <Container
      component="main"
      maxWidth={false}
      sx={{
        maxWidth: designTokens.layout.contentMaxWidth,
        py: { xs: 4, md: 7 },
      }}
    >
      <Box
        sx={{
          display: 'grid',
          gap: { xs: 4, lg: 8 },
          gridTemplateColumns: {
            xs: '1fr',
            lg: 'minmax(0, 1fr) minmax(420px, 0.78fr)',
          },
          minHeight: { lg: 'calc(100vh - 190px)' },
        }}
      >
        <Stack
          sx={{
            alignSelf: 'center',
            display: { xs: 'none', lg: 'flex' },
            gap: 4,
            maxWidth: 600,
          }}
        >
          <Box>
            <Typography color="primary.light" variant="overline">
              EVENTFLOW HESABI
            </Typography>
            <Typography component="p" variant="h2" sx={{ mt: 1.25 }}>
              Etkinlik planların, tek ve güvenilir bir akışta.
            </Typography>
            <Typography color="text.secondary" sx={{ fontSize: 18, mt: 2 }}>
              Keşiften rezervasyona, etkinlik gününe kadar ihtiyacın olan her
              şeyi sade bir deneyimde bul.
            </Typography>
          </Box>
          <Stack component="ul" sx={{ gap: 2, listStyle: 'none', m: 0, p: 0 }}>
            {benefits.map((benefit) => (
              <Stack
                component="li"
                direction="row"
                key={benefit}
                sx={{ alignItems: 'center', gap: 1.5 }}
              >
                <Box
                  aria-hidden="true"
                  sx={{
                    alignItems: 'center',
                    bgcolor: 'action.selected',
                    border: '1px solid',
                    borderColor: 'primary.dark',
                    borderRadius: 999,
                    color: 'primary.light',
                    display: 'inline-flex',
                    flexShrink: 0,
                    fontWeight: 900,
                    height: 28,
                    justifyContent: 'center',
                    width: 28,
                  }}
                >
                  ✓
                </Box>
                <Typography sx={{ fontWeight: 680 }}>{benefit}</Typography>
              </Stack>
            ))}
          </Stack>
        </Stack>

        <Box sx={{ alignSelf: 'center', width: '100%' }}>
          <Box sx={{ mb: 3.5 }}>
            <Typography color="primary.light" variant="overline">
              {footer === 'login' ? 'HESABINA DÖN' : 'YENİ HESAP'}
            </Typography>
            <Typography component="h1" variant="h3" sx={{ mt: 0.75 }}>
              {title}
            </Typography>
            <Typography color="text.secondary" sx={{ mt: 1.25 }}>
              {description}
            </Typography>
          </Box>
          <Surface sx={{ p: { xs: 2.5, sm: 4 } }}>
            {children}
            <Typography
              color="text.secondary"
              sx={{ mt: 3.5, textAlign: 'center' }}
            >
              {footer === 'login'
                ? 'Hesabınız yok mu? '
                : 'Zaten hesabınız var mı? '}
              <Link to={footer === 'login' ? '/register' : '/login'}>
                {footer === 'login' ? 'Ücretsiz kaydolun' : 'Giriş yapın'}
              </Link>
            </Typography>
          </Surface>
        </Box>
      </Box>
    </Container>
  )
}
