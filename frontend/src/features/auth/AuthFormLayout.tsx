import { Link } from '@tanstack/react-router'
import { Box, Card, CardContent, Container, Typography } from '@mui/material'
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
    <Container component="main" maxWidth="sm" sx={{ py: { xs: 5, md: 9 } }}>
      <Box
        sx={{
          mx: 'auto',
          width: '100%',
        }}
      >
        <Box sx={{ mb: 3.5, textAlign: 'center' }}>
          <Typography
            component="p"
            color="primary.main"
            sx={{
              fontSize: '0.78rem',
              fontWeight: 850,
              letterSpacing: '0.12em',
            }}
          >
            EVENTFLOW HESABI
          </Typography>
          <Typography component="h1" variant="h2" sx={{ mt: 1 }}>
            {title}
          </Typography>
          <Typography color="text.secondary" sx={{ mt: 1.25 }}>
            {description}
          </Typography>
        </Box>
        <Card variant="outlined" sx={{ width: '100%' }}>
          <CardContent sx={{ p: { xs: 3, sm: 4.5 } }}>
            {children}
            <Typography
              color="text.secondary"
              sx={{ mt: 3.5, textAlign: 'center' }}
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
