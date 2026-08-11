import { Link } from '@tanstack/react-router'
import { Button, Container, Typography } from '@mui/material'

export function ForbiddenPage() {
  return (
    <Container
      component="main"
      maxWidth="sm"
      sx={{ py: 10, textAlign: 'center' }}
    >
      <Typography component="p" color="primary" sx={{ fontWeight: 800 }}>
        403
      </Typography>
      <Typography component="h1" variant="h2" sx={{ mt: 1 }}>
        Bu işlem için yetkiniz yok
      </Typography>
      <Typography color="text.secondary" sx={{ mt: 2 }}>
        Bu sayfayı görüntülemek için farklı bir hesapla giriş yapmanız
        gerekebilir.
      </Typography>
      <Button component={Link} to="/" variant="contained" sx={{ mt: 4 }}>
        Etkinliklere dön
      </Button>
    </Container>
  )
}
