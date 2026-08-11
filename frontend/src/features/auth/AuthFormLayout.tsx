import { Link } from '@tanstack/react-router'
import { Box, Container, Typography } from '@mui/material'
import type { PropsWithChildren } from 'react'

import { designTokens } from '../../app/theme'
import { Surface } from '../../shared/ui/Surface'

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
          alignItems: 'center',
          display: 'flex',
          justifyContent: 'center',
          minHeight: { lg: 'calc(100vh - 190px)' },
        }}
      >
        <Box sx={{ width: '100%', maxWidth: 520 }}>
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
