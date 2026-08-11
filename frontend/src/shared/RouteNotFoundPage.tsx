import { Link } from '@tanstack/react-router'
import { Button, Container, Typography } from '@mui/material'

export function RouteNotFoundPage() {
  return (
    <Container
      component="main"
      maxWidth="sm"
      sx={{ py: 10, textAlign: 'center' }}
    >
      <Typography component="p" color="primary" sx={{ fontWeight: 800 }}>
        404
      </Typography>
      <Typography component="h1" variant="h2" sx={{ mt: 1 }}>
        Sayfa bulunamadı
      </Typography>
      <Typography color="text.secondary" sx={{ mt: 2 }}>
        Adres değişmiş, içerik kaldırılmış veya bağlantı hatalı olabilir.
      </Typography>
      <Button component={Link} to="/" variant="contained" sx={{ mt: 4 }}>
        Etkinliklere dön
      </Button>
    </Container>
  )
}
