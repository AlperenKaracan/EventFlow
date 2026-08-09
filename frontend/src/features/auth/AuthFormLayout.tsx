import { Link } from '@tanstack/react-router'
import { Card, CardContent, Container, Typography } from '@mui/material'
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
    <Container component="main" maxWidth="sm" sx={{ py: { xs: 4, md: 8 } }}>
      <Card variant="outlined">
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
    </Container>
  )
}
